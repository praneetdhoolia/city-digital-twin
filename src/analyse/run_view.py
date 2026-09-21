#!/usr/bin/env python
"""A live view of a MATSim run in flight, driven by the run's own telemetry.

`replay_events.py` answers *what did the run do* once it is over. This answers
*what is it doing now*, and unlike the view it replaces it does not have to
guess: `src/java/citysim/RunTelemetry.java` publishes the counts and the
per-link congestion from inside the mobsim, so this is a reader, not an
inferrer.

**What is live and what is not, stated rather than implied.** The mobsim sweeps
a 30 h simulated day in about 15 s of wall clock and then goes quiet for the
replanning and scoring that fill the rest of the iteration. So:

  * the simulated clock, the per-mode counts and the per-vehicle-type counts
    update through that sweep, roughly twice a second at the shipped
    `RUN.telemetry.live_interval_s` of one simulated hour;
  * the telemetry file carries the ACCUMULATING PROFILE of the day, not a single
    instant, so a slow poll misses nothing between two reads;
  * the congestion map is live too. It publishes on the same simulated-time
    boundary, and each frame is the WINDOW THAT JUST CLOSED rather than a running
    mean - a cumulative mean converges as the day proceeds, so the peak would
    build and then never dissipate.

**The server is an observer.** It reads the run directory, holds no lock, opens
nothing the run is writing and never writes to it, so a run observed is
byte-for-byte a run unobserved. That property was earned rather than assumed: on
Windows a reader holding `telemetry_links.json` open makes the writer's
`Files.move` throw, and the first version let that exception out of the handler
and **killed the run at iteration 5**. The writer is now structurally unable to
reach the mobsim (DECISIONS.md 9.36), and this reader polls twice a second
against it without incident - measured at 1,987 reads, zero failures.

**Nothing here is a result.** Counts are legs in flight during one iteration,
which is neither the mode agents CHOSE (`modestats.csv`) nor the trips that
COMPLETED (`_metrics.json`) - DECISIONS.md 9.12. `extract_metrics.py` ->
`fit.py` remains the only route to a reportable number.

    python src/analyse/run_view.py --run S2_WEEKDAY_f01_i1000_s20260810
"""
import os
import re
import sys
import collections
import csv
import json
import time
import argparse
import datetime
import threading
import http.server
import socketserver

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
RESULTS = os.path.join(ROOT, 'results')
import registry as _registry  # noqa: E402
import city as _city  # noqa: E402

# a run name resolves through the results store - results/raw first, then a
# legacy top-level dir - so consumers survived the 9.137 layout change once,
# here, instead of each composing its own results/ path
import results_store as _results_store  # noqa: E402


def _resolve_run(name_or_path):
    return _results_store.resolve(name_or_path) or name_or_path


import summarise_run as _summarise  # noqa: E402

ITER_RE = re.compile(r'^(\S+)\s+INFO AbstractController.*ITERATION (\d+) BEGINS')
LAST_ITER_RE = re.compile(r'name="lastIteration" value="(\d+)"')
PARAM_RE = re.compile(r'name="([^"]+)" value="([^"]*)"')
LOG_TS = '%Y-%m-%dT%H:%M:%S,%f'

_CFG = _registry.load()
STALL_S = _CFG.get('RUN.monitor.stall_s')
POLL_S = _CFG.get('RUN.monitor.poll_s')
FAST_POLL_S = _CFG.get('RUN.monitor.live_poll_s')
PORT = _CFG.get('RUN.monitor.port')
# the smallest iteration count the registry admits for a modelling run: below
# it a completed run is a probe, not a result (the sweep's lower bound)
def _horizon_floor():
    # a city that declares its horizon without a sweep (the second city's is a
    # definition) has no floor: every completed run of its is then read as what
    # its record says, never demoted to a probe (build_status_board._horizon_floor)
    try:
        return int(_CFG.sweep('RUN.controler.last_iteration')['interval'][0])
    except Exception:
        return 0


HORIZON_FLOOR = _horizon_floor()

# The colour ramp is FIXED and saturating, never fitted to the data in view.
# Measured on a 1% probe over 59,399 loaded links: median delay ratio 1.10,
# p90 2.58, p95 10.67, max 56,804. A data-driven maximum would let one
# gridlocked hairline flatten the whole city to green. Anything at or above
# RAMP_MAX is simply "stopped", and volume drives width so a link carrying one
# vehicle stays a hairline whatever its ratio. The ramp is a map app's: 1.25
# still green (four fifths of free-flow speed), 1.67 orange, 2.5 red, 4.0
# stop-and-go (a quarter of free-flow speed).
RAMP_MIN = 1.0
RAMP_MAX = 4.0
# The measure the telemetry writes since 15 September 2026 - and, for a payload
# written before it (no `tolerance_s` field), the server applies the same
# correction to the raw mean/free-flow ratio from the network's own lengths
# and speeds. On the routers pair's iteration 28, 35% of loaded links read at
# or past 3.0 on the raw ratio; the median excess over free-flow was 1.4 s and
# the shortest links (free-flow under 2 s, 41,684 of them) had a median ratio
# of 2.62 - the qsim's one-second step read as congestion on every turn stub.
STEP_TOLERANCE_S = 1.0   # the qsim floors the exit to the second and hands over next step
MIN_STRETCH_M = 150.0    # delay is judged over at least a map app's segment, never a stub


def _ts(s):
    try:
        return datetime.datetime.strptime(s, LOG_TS).timestamp()
    except ValueError:
        return None


_ITER_CACHE = {}
_ITER_LOCK = threading.Lock()

# Both markers, so ONE incremental walk of the log serves the live view (which
# wants the BEGINS clock) and the record (which wants BEGINS-to-ENDS).
ITER_MARK_RE = re.compile(
    r'^(\S+)\s+INFO AbstractController.*ITERATION (\d+) (BEGINS|ENDS)')


def read_iterations(log_path):
    """(iteration, wall clock) for every iteration the log has begun.

    INCREMENTAL (#131): the first call walks the log once and every later
    call reads only the bytes appended since, from a saved offset. The
    digest called the whole-file reader twice every 30 s, which at a 25%
    arm's 51 GiB log was about 100 GiB of decoded reads a cycle competing
    with the JVM for the disk. A log that shrinks (a new run in the same
    directory) resets the offset. Thread-safe: the digest and the gate
    watcher share one cache.
    """
    return _read_markers(log_path)[0]


def read_iteration_spans(log_path):
    """{iteration: wall seconds} from BEGINS to ENDS, incrementally.

    The same quantity `run_matsim.iteration_times` reads out of the whole log
    at close-out, from the same two markers - but accumulated as the run goes,
    off the offset the live view is already advancing. The record's
    `median_iteration_s` is this, so the two must agree exactly: an iteration
    appears here only once its ENDS marker has been read, which is the property
    the record needs.
    """
    return _read_markers(log_path)[1]


def _read_markers(log_path):
    """([(iteration, begin clock)], {iteration: span seconds}), incremental.

    ONE walk of the log serves both. The first call reads it once; every later
    call reads only the bytes appended since (#131) - the digest called a
    whole-file reader twice every 30 s, which at a 25% arm's 51 GiB log was
    about 100 GiB of decoded reads a cycle competing with the JVM for the disk.
    A log that shrinks (a new run in the same directory) resets the offset.
    Thread-safe: the digest and the gate watcher share one cache.
    """
    with _ITER_LOCK:
        offset, out, begins, spans = _ITER_CACHE.get(
            log_path, (0, [], {}, {}))
        try:
            size = os.path.getsize(log_path)
        except OSError:
            return [], {}
        if size < offset:
            offset, out, begins, spans = 0, [], {}, {}
        if size == offset:
            return list(out), dict(spans)
        out, begins, spans = list(out), dict(begins), dict(spans)
        try:
            with open(log_path, 'rb') as f:
                f.seek(offset)
                carry = b''
                pos = offset
                while True:
                    chunk = f.read(1 << 24)
                    if not chunk:
                        break
                    buf = carry + chunk
                    lines = buf.split(b'\n')
                    carry = lines.pop()
                    for raw in lines:
                        if b'ITERATION' not in raw:
                            continue
                        if b'BEGINS' not in raw and b'ENDS' not in raw:
                            continue
                        m = ITER_MARK_RE.match(
                            raw.decode('utf-8', errors='replace'))
                        if not m:
                            continue
                        t = _ts(m.group(1))
                        if t is None:
                            continue
                        n = int(m.group(2))
                        if m.group(3) == 'BEGINS':
                            out.append((n, t))
                            begins[n] = t
                        elif n in begins:
                            spans[n] = round(t - begins[n], 2)
                    pos = f.tell() - len(carry)
        except OSError:
            return list(out), dict(spans)
        _ITER_CACHE[log_path] = (pos, out, begins, spans)
        return list(out), dict(spans)


_STAMPED = {}
_STAMPED_LOCK = threading.Lock()


def _stamped(path, reader, *args):
    """`reader(path, *args)` memoised on the file's (size, mtime): a poll re-reads a file
    only when the run has rewritten it. The status poll runs every half second while the
    mobsim sweeps, and every one of these files changes at most once an iteration."""
    try:
        st = os.stat(path)
        key = (st.st_size, st.st_mtime_ns)
    except OSError:
        key = None
    with _STAMPED_LOCK:
        hit = _STAMPED.get((path, args))
        if hit and hit[0] == key:
            return hit[1]
    val = reader(path, *args)
    with _STAMPED_LOCK:
        _STAMPED[(path, args)] = (key, val)
    return val


def read_series(path, keep=None):
    """A MATSim per-iteration csv as {column: [values]}, semicolon-delimited."""
    return _stamped(path, _read_series, None if keep is None else tuple(sorted(keep)))


def _read_series(path, keep):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f, delimiter=';'))
    except OSError:
        return {}
    if not rows:
        return {}
    cols = [c for c in rows[0] if c and c != 'iteration'
            and (keep is None or c in keep)]
    out = {'iteration': [int(float(r['iteration'])) for r in rows]}
    for c in cols:
        vals = []
        for r in rows:
            try:
                vals.append(round(float(r[c]), 6))
            except (TypeError, ValueError):
                vals.append(None)
        out[c] = vals
    return out


def _read_text(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except OSError:
        return ''


def _load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def read_jsonl(path, tail=None):
    """Per-iteration telemetry summaries, ~5 KB each; parsed once per rewrite of the file."""
    return _stamped(path, _read_jsonl, tail)


def _read_jsonl(path, tail):
    out = []
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    # the run may be mid-write on the last line
                    continue
    except OSError:
        return []
    return out[-tail:] if tail else out


def scan(run_dir):
    """Everything the page shows, read fresh from the run directory."""
    name = os.path.basename(os.path.abspath(run_dir))
    log = os.path.join(run_dir, 'matsim.log')
    out_dir = os.path.join(run_dir, 'output')
    record = os.path.join(run_dir, '_run.json')

    cfg_text = _stamped(os.path.join(run_dir, 'config.xml'), _read_text)
    m = LAST_ITER_RE.search(cfg_text)
    target = int(m.group(1)) if m else None
    params = dict(PARAM_RE.findall(cfg_text))

    iters = read_iterations(log)
    current = iters[-1][0] if iters else None
    durations = [(b[1] - a[1]) for a, b in zip(iters, iters[1:])]
    recent = durations[-20:]
    median = round(sorted(recent)[len(recent) // 2], 2) if recent else None

    done = bool(os.path.exists(record))
    run_rec = _load_json(record, {}) if done else {}
    snap = (_load_json(os.path.join(run_dir, '_config.json'), {}) or {}).get('values') or {}

    def ident(key, field):
        v = run_rec.get(key)
        return snap.get(field) if v is None else v

    scenario = run_rec.get('scenario')
    day = run_rec.get('day')
    if scenario is None or day is None:
        m2 = re.search(r'scenarios[/\\]matsim[/\\]([^/\\"]+)[/\\]([^/\\"]+)[/\\]',
                       cfg_text)
        if m2:
            scenario = scenario or m2.group(1)
            day = day or m2.group(2)

    try:
        age = time.time() - os.path.getmtime(log)
    except OSError:
        age = None
    if done:
        # since 9.143 a gate-, ceiling-, stall- or operator-stopped arm
        # carries a record with rc != 0; its `completion` names the boundary
        # and it is not a failure (eighth project report, area 3)
        completion = run_rec.get('completion')
        if run_rec.get('rc') == 0 or completion == 'ran_to_last_iteration':
            state = 'finished'
        elif completion and completion.startswith('stopped_'):
            state = completion
        else:
            state = 'failed'
    elif age is None:
        state = 'starting'
    elif age > STALL_S:
        state = 'stalled'
    else:
        state = 'running'

    remaining = None
    eta_s = None
    if target is not None and current is not None:
        remaining = max(0, target - current)
        if median:
            eta_s = round(remaining * median)
    started = iters[0][1] if iters else None
    elapsed = round(time.time() - started) if started and not done else (
        run_rec.get('wall_s'))

    frac_off = params.get('fractionOfIterationsToDisableInnovation')
    innovation_off = None
    if target is not None and frac_off:
        try:
            import iteration_reading as _reading
            innovation_off = _reading.innovation_off_after(
                params.get('firstIteration') or 0, target, frac_off)
        except ValueError:
            innovation_off = None

    modes = read_series(os.path.join(out_dir, 'modestats.csv'))
    scores = read_series(os.path.join(out_dir, 'scorestats.csv'),
                         keep={'avg_executed', 'avg_best', 'avg_worst'})

    # Has the run settled? The question issue #5 turns on. Delegated to
    # summarise_run so the live view and the finished summary cannot disagree:
    # this page had its own second implementation, in fractions rather than
    # percentage points, and two implementations of one verdict is exactly the
    # drift this package cannot absorb. The tolerance is declared
    # (RUN.relaxation.drift_tolerance_pp), not decided here.
    # the two declared values are passed in: relaxation() would otherwise resolve and
    # validate the whole registry twice on every poll (0.585 s of a 0.628 s scan)
    relaxation = _summarise.relaxation(
        modes, innovation_off,
        tolerance_pp=_CFG.get('RUN.relaxation.drift_tolerance_pp'),
        settle_margin=_CFG.get('RUN.relaxation.settle_margin_iterations'))

    live = _load_json(os.path.join(out_dir, 'telemetry_live.json'))
    history = read_jsonl(os.path.join(out_dir, 'telemetry.jsonl'))
    last_iter = history[-1] if history else None
    links_path = os.path.join(out_dir, 'telemetry_links.json')
    links_iter = links_stamp = None
    if os.path.exists(links_path):
        # mtime rather than a re-read: the payload is up to 1.14 MB and this is
        # polled twice a second while the mobsim sweeps. The file is replaced
        # atomically, so its mtime changes exactly once per published window.
        try:
            links_stamp = os.path.getmtime(links_path)
        except OSError:
            links_stamp = None

    # Has the run got telemetry at all? A run assembled before the module
    # existed has none, and the page must say so rather than showing zeroes.
    telemetry = live is not None or last_iter is not None

    meta = _load_json(os.path.join(run_dir, '_meta.json'), {}) or {}

    def declared(field):
        v = snap.get(field)
        try:
            return None if v is None else float(v)
        except (TypeError, ValueError):
            return None

    return {
        'name': name,
        'state': state,
        'status': meta.get('status'),
        'completion': run_rec.get('completion') if done else None,
        'cause': meta.get('cause'),
        'started': meta.get('started'),
        'ended': meta.get('ended'),
        'persons_kept': (meta.get('sample') or {}).get('persons_kept'),
        'gate_interval': declared('RUN.gate.interval_iterations'),
        'wall_ceiling_h': declared('RUN.gate.wall_ceiling_h'),
        'xmx': meta.get('xmx'),
        'horizon_floor': HORIZON_FLOOR,
        'scenario': scenario,
        'day': day,
        'fraction': ident('fraction', 'RUN.sample.fraction'),
        'seed': ident('seed', 'RUN.machine.seed'),
        'threads': ident('threads', 'RUN.machine.threads'),
        'controler_sha256': run_rec.get('controler_sha256'),
        'iteration': current,
        'target': target,
        'remaining': remaining,
        'median_iteration_s': median,
        'last_iteration_s': round(durations[-1], 2) if durations else None,
        'eta_s': eta_s,
        'elapsed_s': elapsed,
        'innovation_off_at': innovation_off,
        'relaxation': relaxation,
        'modes': modes,
        'scores': scores,
        'telemetry': telemetry,
        'live': live,
        'last_iteration': last_iter,
        'links_iteration': links_iter,
        'links_stamp': links_stamp,
        'ramp': {'min': RAMP_MIN, 'max': RAMP_MAX},
        'log_age_s': round(age) if age is not None else None,
        'rc': run_rec.get('rc'),
        'served_at': time.time(),
    }


# ---------------------------------------------------------------- the runs

def _families():
    """The family ledger, parsed once per change of the file it lives in."""
    try:
        import build_run_index as _index
        return _stamped(_city.docs('run_families.json'), lambda _p: _index.load_families())
    except Exception:                                        # noqa: BLE001
        return [], {}


_RUNS_CACHE = {}


def list_runs():
    """Every run the store holds, newest first, with what the index knows.

    The page offers them in a picker, so one server observes any run on disk
    rather than the one it was started for. Read from each run's own records
    only - never from the board. Walking 192 run directories reads ~16,000
    files, so the list is kept for a minute and rebuilt at once when a run
    directory appears or goes.
    """
    roots = []
    for root in (_results_store.RAW, _results_store.PROCESSED):
        try:
            roots.append(os.stat(root).st_mtime_ns)
        except OSError:
            roots.append(None)
    key = tuple(roots)
    hit = _RUNS_CACHE.get('runs')
    if hit and hit[0] == key and time.time() - hit[1] < 60:
        return hit[2]
    out = _list_runs()
    _RUNS_CACHE['runs'] = (key, time.time(), out)
    return out


def _list_runs():
    import build_run_index as _index
    fams, overrides = _families()
    out = []
    def stamp(name):
        return name[len('aborted_'):] if name.startswith('aborted_') else name

    for name in sorted(_results_store.run_names(), key=stamp, reverse=True):
        run_dir = _results_store.resolve_records(name)
        if not run_dir:
            continue
        meta = _load_json(os.path.join(run_dir, '_meta.json'), {}) or {}
        record = _load_json(os.path.join(run_dir, '_run.json'))
        family = None
        try:
            family, _ = _index.family_of(name, fams, overrides)
        except Exception:                                    # noqa: BLE001
            pass
        completion = (record or {}).get('completion')
        if record is not None and not completion:
            completion = 'ran_to_last_iteration'
        out.append({
            'name': name,
            'status': meta.get('status') or ('completed' if record else 'unknown'),
            'completion': completion,
            'reached': (record or {}).get('reached_iteration')
                       or (record or {}).get('iterations'),
            'iterations': meta.get('iterations'),
            'fraction': meta.get('fraction'),
            'scenario': meta.get('scenario'),
            'day': meta.get('day'),
            'family': family,
            'raw_on_disk': bool(_results_store.raw_dir(name)
                                and os.path.isdir(_results_store.raw_dir(name))),
            # a result is a run that executed the horizon it declared; whether
            # that horizon is a modelling one is the registry's sweep floor,
            # not a number typed here
            'is_result': completion == 'ran_to_last_iteration'
                         and (meta.get('iterations') or 0) >= HORIZON_FLOOR,
        })
    return out


def family_of_run(name):
    try:
        import build_run_index as _index
        fams, overrides = _families()
        return _index.family_of(name, fams, overrides)[0]
    except Exception:                                        # noqa: BLE001
        return None


# ---------------------------------------------------------------- the twelve modes

READINGS = '_readings.jsonl'        # appended by the runner's gate watcher
GATE_VERDICT = '_gate_verdict.json'  # the reporter's last verdict, rows included

_MODES_LOCK = threading.Lock()
_MODES_CACHE = collections.OrderedDict()   # (run_dir, iteration) -> reading dict, bounded
_MODES_BUSY = set()     # (run_dir, iteration) being computed on the one worker thread
_MODES_QUEUE = []       # readings asked for while the worker is busy, in order
MODES_CACHE_ENTRIES = 64
REPORTER = os.path.join(_HERE, 'report_mode_ridership.py')


def _reporter():
    import report_mode_ridership as _rmr
    return _rmr


def mode_targets():
    """Every mode's target on its own basis, from the city's artefact."""
    rmr = _reporter()
    out = []
    for i, (mode, t) in enumerate(rmr.load_targets().items(), 1):
        out.append(dict(n=i, mode=mode, target=t.get('target'), low=t.get('low'),
                        high=t.get('high'), mean_km=t.get('mean_km'),
                        denominator=t.get('denominator') or '',
                        status=t.get('status'), basis=t.get('basis') or ''))
    return out


def readable_iterations(run_dir):
    """Iterations with a trips table or experienced plans, ascending."""
    try:
        import measure_iteration_modes as _mim
        import iteration_trips as _itr
        return sorted(set(_mim.iterations_with_trips(run_dir))
                      | set(_itr.iterations_with_plans(run_dir)))
    except Exception:                                        # noqa: BLE001
        return []


def stored_readings(run_dir):
    """{iteration: reading} the runner wrote for this run - the ledger the gate
    watcher appends at every milestone, plus its last verdict when that
    carries rows. Nothing is computed here."""
    out = {}
    for doc in read_jsonl(os.path.join(run_dir, READINGS)):
        if isinstance(doc, dict) and doc.get('rows') and doc.get('iteration') is not None:
            out[int(doc['iteration'])] = doc
    v = _load_json(os.path.join(run_dir, GATE_VERDICT))
    if isinstance(v, dict) and v.get('rows') and v.get('iteration') is not None:
        out.setdefault(int(v['iteration']), v)
    return out


def _compute_reading(run_dir, iteration):
    """The reporter run as a SUBPROCESS writing `--json` to a temporary file.

    Never in-process: the reporter prints its table to stdout and keeps its
    rows in a module global, and this server may be living inside the
    runner's own process (`run_matsim.start_live_view`), where redirecting
    sys.stdout would swallow the gate, ceiling and stall watchers' prints and
    two overlapped readings would race on one dict (tenth report, defects 1
    and 2). A subprocess owns its stdout and its globals. Writes nothing to
    the run directory.
    """
    import subprocess
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix='reading_', suffix='.json')
    os.close(fd)
    try:
        out = subprocess.run([sys.executable, REPORTER, '--run', run_dir,
                              '--it', str(iteration), '--json', tmp],
                             capture_output=True, text=True, timeout=1800, cwd=ROOT)
        if out.returncode != 0:
            tail = (out.stderr or out.stdout or '').strip().splitlines()
            return {'iteration': iteration, 'error': tail[-1] if tail else 'reporter rc=%d' % out.returncode}
        doc = _load_json(tmp)
        if not isinstance(doc, dict) or not doc.get('rows'):
            return {'iteration': iteration, 'error': 'the reporter wrote no rows'}
        text = out.stdout
        breaches = []
        if 'GATE:' in text and 'at or past' in text:
            breaches = [r['mode'] for r in doc['rows']
                        if r.get('flag', '').startswith('STOP')]
        doc.update(passed=not breaches, breaches=breaches,
                   read_at=time.strftime('%Y-%m-%dT%H:%M:%S'),
                   computed_by='run_view (a reporter subprocess; not written to the run)')
        return doc
    except (OSError, subprocess.SubprocessError) as exc:
        return {'iteration': iteration, 'error': '%s: %s' % (exc.__class__.__name__, exc)}
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _worker():
    """One reading at a time: a 25 % trips table is a ~20 s read of a few
    hundred MB, and two of them at once compete with the run for the disk."""
    while True:
        with _MODES_LOCK:
            if not _MODES_QUEUE:
                _MODES_BUSY.discard('worker')
                return
            key = _MODES_QUEUE.pop(0)
        doc = _compute_reading(*key)
        with _MODES_LOCK:
            _MODES_CACHE[key] = doc
            while len(_MODES_CACHE) > MODES_CACHE_ENTRIES:
                _MODES_CACHE.popitem(last=False)
            _MODES_BUSY.discard(key)


def _start_reading(run_dir, iteration):
    key = (run_dir, iteration)
    with _MODES_LOCK:
        if key in _MODES_CACHE or key in _MODES_BUSY:
            return
        _MODES_BUSY.add(key)
        _MODES_QUEUE.append(key)
        if 'worker' in _MODES_BUSY:
            return
        _MODES_BUSY.add('worker')
    threading.Thread(target=_worker, daemon=True, name='mode-reading').start()


def modes(run_dir, iteration=None, compute=True):
    """The twelve modes against their targets: every stored reading, and the
    requested (default newest readable) iteration computed on a thread when
    the runner has not written it. `computing` says a reading is on its way."""
    rmr = _reporter()
    targets = mode_targets()
    # the reporter and the targets are the server's city's: a run of another
    # city (the picker offers every city's) is not read against them
    if run_city(run_dir) != _city.CITY:
        return {'targets': {}, 'stop_pct': rmr.GATE_STOP_PCT, 'pass_pct': rmr.GATE_PASS_PCT,
                'readable': [], 'stored': [], 'requested': None, 'computing': False, 'trend': {},
                'current': {'error': 'a %s run: its modes are read by a viewer serving that city '
                                     '(CITYSIM_CITY=%s python src/analyse/run_view.py --run %s)'
                                     % (run_city(run_dir), run_city(run_dir), os.path.basename(run_dir))}}
    stored = stored_readings(run_dir)
    readable = readable_iterations(run_dir)
    run_dir = os.path.abspath(run_dir)
    with _MODES_LOCK:
        for (rd, it), doc in _MODES_CACHE.items():
            if rd == run_dir:
                stored.setdefault(it, doc)
    want = iteration if iteration is not None else (readable[-1] if readable else None)
    computing = False
    if want is not None and want not in stored and compute and want in readable:
        _start_reading(run_dir, want)
        with _MODES_LOCK:
            computing = (run_dir, want) in _MODES_BUSY
    current = stored.get(want) if want is not None else None
    if current is None and stored:
        current = stored[max(stored)]
    ordered = [stored[k] for k in sorted(stored)]
    trend = {}
    for doc in ordered:
        for r in doc.get('rows') or []:
            trend.setdefault(r['mode'], []).append([doc['iteration'], r.get('deviation_pct')])
    return {
        'targets': targets,
        'stop_pct': rmr.GATE_STOP_PCT,
        'pass_pct': rmr.GATE_PASS_PCT,
        'readable': readable,
        'stored': sorted(stored),
        'requested': want,
        'computing': computing,
        'current': current,
        'trend': trend,
    }


# ---------------------------------------------------------------- the map

_NET_CACHE = collections.OrderedDict()   # run_dir -> network doc; a few runs at most
_NET_LOCK = threading.Lock()
NET_CACHE_ENTRIES = 2        # ~130 MB of Python objects per 368,000-link network
_BASEMAP_CACHE = {}
_TRANSFORMERS = {}


def run_city(run_dir):
    """The city a run belongs to: its own record's `city` (9.204), else the
    server's city for a record written before the field existed."""
    meta = _load_json(os.path.join(run_dir, '_meta.json')) or {}
    return meta.get('city') or _city.CITY


def _to_wgs84(run_dir=None):
    """A city's projected CRS -> WGS84 lon/lat, built once per city.

    THE RUN'S city, never the server's: the results store holds every city's
    runs and the picker offers them all, and a Mumbai run read through the
    reference city's MGA zone 56 landed in the Southern Ocean off Antarctica
    (the user's report, 22 September 2026, 9.206) - UTM zone 43N metres are
    valid MGA 56 metres, so nothing failed, the map just drew it 100 degrees
    of longitude away. The CRS is the run's city's `city.json`.
    """
    name = run_city(run_dir) if run_dir else _city.CITY
    if name not in _TRANSFORMERS:
        from pyproj import Transformer
        crs = 'EPSG:%d' % _city.descriptor(name)['crs']['epsg']
        _TRANSFORMERS[name] = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
    return _TRANSFORMERS[name]


def _input_network(run_dir):
    """Resolve `inputNetworkFile` from the run's config, else the output copy."""
    cfg = os.path.join(run_dir, 'config.xml')
    try:
        with open(cfg, encoding='utf-8') as f:
            m = re.search(r'name="inputNetworkFile" value="([^"]+)"', f.read())
    except OSError:
        m = None
    if m:
        p = m.group(1)
        if not os.path.isabs(p):
            p = os.path.join(run_dir, p)
        if os.path.exists(p):
            return p
    fallback = os.path.join(run_dir, 'output', 'output_network.xml.gz')
    return fallback if os.path.exists(fallback) else None


def load_network(run_dir):
    """The run's OWN network as {link id: (lon0, lat0, lon1, lat1)}, plus a
    stable index over the ids, cached by the file's stamp.

    The traffic overlay is keyed by MATSim link id, so its geometry comes from
    the network the run drove - the INPUT network, which exists before the
    first iteration (MATSim writes output_network.xml.gz only at the end).
    Reprojected here, once, so the page draws in the same frame as the tiles.
    """
    import gzip
    path = _input_network(run_dir)
    if not path:
        return None
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    with _NET_LOCK:
        hit = _NET_CACHE.get(run_dir)
        if hit and hit['stamp'] == stamp:
            return hit
    node_re = re.compile(r'<node id="([^"]+)" x="([^"]+)" y="([^"]+)"')
    link_re = re.compile(r'<link id="([^"]+)" from="([^"]+)" to="([^"]+)"')
    len_re = re.compile(r' length="([^"]+)"')
    spd_re = re.compile(r' freespeed="([^"]+)"')
    nodes, links, ff, speed = {}, [], {}, {}
    try:
        with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
            for line in f:
                m = node_re.search(line)
                if m:
                    nodes[m.group(1)] = (float(m.group(2)), float(m.group(3)))
                    continue
                m = link_re.search(line)
                if m:
                    links.append((m.group(1), m.group(2), m.group(3)))
                    # length and speed, for the delay measure on payloads written before it
                    ml, ms = len_re.search(line), spd_re.search(line)
                    if ml and ms:
                        try:
                            v = float(ms.group(1))
                            speed[m.group(1)] = v
                            ff[m.group(1)] = float(ml.group(1)) / v if v > 0 else 0.0
                        except ValueError:
                            pass
    except (OSError, ValueError):
        return None
    ids, xs, ys = [], [], []
    for lid, a, b in links:
        pa, pb = nodes.get(a), nodes.get(b)
        if pa and pb:
            ids.append(lid)
            xs += [pa[0], pb[0]]
            ys += [pa[1], pb[1]]
    lons, lats = _to_wgs84(run_dir).transform(xs, ys)
    geom = {}
    index = {}
    for i, lid in enumerate(ids):
        geom[lid] = (lons[2 * i], lats[2 * i], lons[2 * i + 1], lats[2 * i + 1])
        index[lid] = i
    doc = {'stamp': stamp, 'path': path, 'ids': ids, 'geom': geom, 'index': index,
           'ff': ff, 'speed': speed}
    with _NET_LOCK:
        _NET_CACHE[run_dir] = doc
        while len(_NET_CACHE) > NET_CACHE_ENTRIES:
            _NET_CACHE.popitem(last=False)
    return doc


_ROUTES_CACHE = collections.OrderedDict()   # run_dir -> routes doc, cached by the schedule's stamp
_ROUTES_LOCK = threading.Lock()


def _input_schedule(run_dir):
    """Resolve `transitScheduleFile` from the run's config, else the output copy."""
    cfg = os.path.join(run_dir, 'config.xml')
    try:
        with open(cfg, encoding='utf-8') as f:
            m = re.search(r'name="transitScheduleFile" value="([^"]+)"', f.read())
    except OSError:
        m = None
    if m and m.group(1) not in ('null', ''):
        p = m.group(1)
        if not os.path.isabs(p):
            p = os.path.join(run_dir, p)
        if os.path.exists(p):
            return p
    fallback = os.path.join(run_dir, 'output', 'output_transitSchedule.xml.gz')
    return fallback if os.path.exists(fallback) else None


def load_routes(run_dir):
    """Every transit route of the run's OWN schedule as a polyline over the run's
    own network, grouped by transport mode: {mode: {'names': [...], 'lines': [...],
    'counts': [...], 'coords': [lon, lat, ...]}}, cached by the schedule's stamp.

    The schedule is whatever the city mapped - bus, rail, subway, tram, ferry, or
    a mode of its own naming - so nothing here knows a mode by name: the modes are
    read off the `<transportMode>` elements and handed to the page as they are.
    A route's geometry is the chain of its mapped links (`<route><link refId/>`),
    drawn from the network the run drove, so a ferry mapped onto a water link is
    drawn on that link. Two routes of one line over the same links (the departures
    of a pattern) are one polyline; a route with no mapped links (a stop-to-stop
    pattern the mapper could not place) is counted and skipped.
    """
    import gzip
    import xml.etree.ElementTree as ET
    path = _input_schedule(run_dir)
    net = load_network(run_dir)
    if not path or not net:
        return None
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return None
    with _ROUTES_LOCK:
        hit = _ROUTES_CACHE.get(run_dir)
        if hit and hit['stamp'] == stamp and hit['net_stamp'] == net['stamp']:
            return hit
    geom = net['geom']
    modes = {}
    seen = set()
    unplaced = 0
    line_id = line_name = None
    try:
        with gzip.open(path, 'rb') as f:
            for ev, el in ET.iterparse(f, events=('start', 'end')):
                tag = el.tag.rsplit('}', 1)[-1]
                if ev == 'start' and tag == 'transitLine':
                    line_id, line_name = el.get('id'), el.get('name') or el.get('id')
                    continue
                if ev != 'end' or tag != 'transitRoute':
                    continue
                mode = (el.findtext('transportMode') or 'pt').strip()
                links = [lk.get('refId') for lk in el.iter() if lk.tag.rsplit('}', 1)[-1] == 'link']
                key = (mode, tuple(links))
                if not links or key in seen:
                    if not links:
                        unplaced += 1
                    el.clear()
                    continue
                seen.add(key)
                coords = []
                for lid in links:
                    g = geom.get(lid)
                    if not g:
                        continue
                    if not coords:
                        coords += [g[0], g[1]]
                    coords += [g[2], g[3]]
                if len(coords) >= 4:
                    m = modes.setdefault(mode, {'names': [], 'lines': [], 'counts': [], 'coords': []})
                    m['names'].append(line_name)
                    m['lines'].append(line_id)
                    m['counts'].append(len(coords) // 2)
                    m['coords'] += coords
                el.clear()
    except (OSError, ET.ParseError):
        return None
    doc = {'stamp': stamp, 'net_stamp': net['stamp'], 'path': path, 'modes': modes,
           'unplaced_routes': unplaced}
    with _ROUTES_LOCK:
        _ROUTES_CACHE[run_dir] = doc
        while len(_ROUTES_CACHE) > NET_CACHE_ENTRIES:
            _ROUTES_CACHE.popitem(last=False)
    return doc


def routes_summary(run_dir):
    """What the page asks first: which transport modes the schedule carries and
    how many distinct routes each has; the geometry comes per mode on request."""
    doc = load_routes(run_dir)
    if not doc:
        return {'available': False, 'reason': 'no schedule or network readable for this run'}
    return {'available': True, 'stamp': doc['stamp'], 'unplaced_routes': doc['unplaced_routes'],
            'modes': {m: {'routes': len(v['counts']), 'vertices': len(v['coords']) // 2}
                      for m, v in sorted(doc['modes'].items())}}


def routes_geojson(run_dir, mode):
    """One transport mode's routes as a FeatureCollection of LineStrings, each
    carrying its line's id and name, built once per schedule stamp."""
    doc = load_routes(run_dir)
    if not doc or mode not in doc['modes']:
        return '{"type":"FeatureCollection","features":[]}'
    cache = doc.setdefault('_geojson', {})
    if mode not in cache:
        m = doc['modes'][mode]
        feats = []
        v = 0
        for name, line, n in zip(m['names'], m['lines'], m['counts']):
            pts = [[round(m['coords'][2 * (v + k)], 6), round(m['coords'][2 * (v + k) + 1], 6)] for k in range(n)]
            v += n
            feats.append({'type': 'Feature', 'properties': {'name': name, 'line': line, 'mode': mode},
                          'geometry': {'type': 'LineString', 'coordinates': pts}})
        cache[mode] = json.dumps({'type': 'FeatureCollection', 'features': feats}, separators=(',', ':'))
    return cache[mode]


def _pack(fmt, vals):
    import array
    a = array.array(fmt, vals)
    if sys.byteorder != 'little':
        a.byteswap()
    return a.tobytes()


def _b64(fmt, vals):
    import base64
    return base64.b64encode(_pack(fmt, vals)).decode('ascii')


def network_bytes(run_dir):
    """Every link's endpoints, once per network: Float32 lon/lat in link-index
    order, about 6 MB for a 368,000-link network, packed once and kept on the
    network document. The page reads the bytes straight into a Float32Array."""
    net = load_network(run_dir)
    if not net:
        return None
    if 'bytes' not in net:
        coords = []
        for lid in net['ids']:
            coords += net['geom'][lid]
        net['bytes'] = _pack('f', coords)
    return net


def _volume_bbox(rows, keep):
    """The box holding `keep` of all traversals, trimmed equally from each side."""
    total = sum(v for _, v, _ in rows)
    if total <= 0:
        return None
    drop = total * (1.0 - keep) / 2.0
    out = []
    for axis in (0, 1):
        pts = sorted(((g[axis] + g[axis + 2]) / 2.0, v) for g, v, _ in rows)
        acc, lo, hi = 0.0, pts[0][0], pts[-1][0]
        for c, v in pts:
            acc += v
            if acc >= drop:
                lo = c
                break
        acc = 0.0
        for c, v in reversed(pts):
            acc += v
            if acc >= drop:
                hi = c
                break
        out.append((lo, hi))
    return [out[0][0], out[1][0], out[0][1], out[1][1]]


_HOTSPOT_CACHE = {}


def delay_ratio(raw_ratio, freeflow_s, speed_mps):
    """The delay ratio the telemetry writes since 15 September 2026, computed here
    from a raw mean/free-flow ratio: the delay past the free-flow traversal and the
    qsim's one-second step, over at least the free-flow time of MIN_STRETCH_M at
    the link's speed. A link with no length or speed reads 1.0 (flowing)."""
    if freeflow_s <= 0 or speed_mps <= 0:
        return 1.0
    delay = max(0.0, raw_ratio * freeflow_s - freeflow_s - STEP_TOLERANCE_S)
    return 1.0 + delay / max(freeflow_s, MIN_STRETCH_M / speed_mps)


def hotspot(run_dir):
    """The window's per-link congestion, keyed to the network payload's index:
    link index (uint32), vehicle volume (uint16) and the delay ratio on the
    fixed ramp (uint16), so a window costs six bytes a loaded link rather
    than a re-sent geometry. The join to geometry stays here, not in the page,
    and is done once per published window: the file is replaced atomically, so
    its stamp names the window."""
    path = os.path.join(run_dir, 'output', 'telemetry_links.json')
    try:
        st = os.stat(path)
        key = (st.st_size, st.st_mtime_ns)
    except OSError:
        key = None
    hit = _HOTSPOT_CACHE.get(run_dir)
    if hit and hit[0] == key:
        return hit[1]
    doc = _hotspot(run_dir, path)
    if doc.get('available'):
        _HOTSPOT_CACHE[run_dir] = (key, doc)
    return doc


def _hotspot(run_dir, path):
    payload = _load_json(path)
    if not payload:
        return {'available': False,
                'reason': 'no telemetry_links.json - this run was assembled '
                          'before the telemetry module existed, or has not '
                          'finished an iteration'}
    net = load_network(run_dir)
    if not net:
        return {'available': False,
                'reason': 'the run network could not be read - neither '
                          'inputNetworkFile from config.xml nor '
                          'output/output_network.xml.gz'}
    index, geom = net['index'], net['geom']
    # a payload written before the telemetry measured delay this way carries the raw
    # mean/free-flow ratio; the same correction is applied here from the network
    measured = payload.get('tolerance_s') is not None
    ff, speed = net.get('ff') or {}, net.get('speed') or {}

    def corrected(lid, ratio):
        return ratio if measured else delay_ratio(ratio, ff.get(lid, 0.0), speed.get(lid, 0.0))
    # [id, volume, ratio] from the telemetry before 15 September 2026; since then
    # [id, volume, typical, mean] - the typical (median) traversal's delay is the colour
    rows = [(geom[r[0]], r[1], corrected(r[0], r[2]), index[r[0]])
            for r in payload['links'] if r[0] in index]
    if not rows:
        return {'available': False, 'reason': 'no loaded link matched the network'}
    idx, vols, ratios = [], [], []
    vmax = max(v for _, v, _, _ in rows) or 1
    for g, vol, ratio, i in rows:
        idx.append(i)
        vols.append(min(65535, int(vol)))
        t = (min(max(ratio, RAMP_MIN), RAMP_MAX) - RAMP_MIN) / (RAMP_MAX - RAMP_MIN)
        ratios.append(int(t * 65535))
    lons = [c for g, _, _, _ in rows for c in (g[0], g[2])]
    lats = [c for g, _, _, _ in rows for c in (g[1], g[3])]
    # the default view is the box holding the middle 90% of TRAVERSALS - the
    # scale of the five-LGA study area - because a fraction of a percent of
    # very long external trips is enough to drag the frame off the city
    core = _volume_bbox([(g, v, r) for g, v, r, _ in rows], 0.90)
    # the same links as GeoJSON text for the GL page's worker: the delay ratio itself as
    # `d`, capped at the ramp's top, volume as `v` = sqrt(volume / max) in [0, 1], six
    # decimals of degree. Built here, once per window, so the page never assembles or
    # stringifies a feature.
    parts = []
    for g, vol, ratio, _ in rows:
        parts.append('{"type":"Feature","properties":{"d":%.2f,"v":%.2f},"geometry":{"type":"LineString","coordinates":[[%.6f,%.6f],[%.6f,%.6f]]}}'
                     % (min(max(ratio, RAMP_MIN), RAMP_MAX), (vol / vmax) ** 0.5, g[0], g[1], g[2], g[3]))
    geojson = ('{"type":"FeatureCollection","features":[' + ','.join(parts) + ']}').encode('utf-8')
    return {
        'available': True,
        'stamp': net['stamp'],
        '_geojson': geojson,
        'iteration': payload.get('iteration'),
        'scope': payload.get('scope', 'iteration'),
        'window_from': payload.get('window_from'),
        'window_to': payload.get('window_to'),
        'window_from_s': payload.get('window_from_s'),
        'window_to_s': payload.get('window_to_s'),
        'metric': payload.get('metric'),
        'measure': ('the telemetry\'s, %s traversal' % payload.get('statistic', 'mean') if measured
                    else 'corrected here from the network, mean traversal')
                   + ': delay past free-flow and a %.0f s step, over at least %.0f m' % (STEP_TOLERANCE_S, MIN_STRETCH_M),
        'covers': payload.get('covers'),
        'n_links': len(rows),
        'bbox': [min(lons), min(lats), max(lons), max(lats)],
        'core_bbox': core,
        'volume_max': vmax,
        'ramp': [RAMP_MIN, RAMP_MAX],
        'index': _b64('I', idx),
        'volume': _b64('H', vols),
        'delay': _b64('H', ratios),
    }


def basemap_bytes(run_dir=None):
    """`basemap_payload` as one binary body: a little-endian uint32 header length, the
    header JSON ({layer: {polylines, coords, area}} in order), then per layer its
    uint32 vertex counts and Float32 lon/lat pairs. Built once per basemap file."""
    doc = basemap_payload(run_dir)
    if not doc.get('available'):
        return None
    if '_bytes' not in doc:
        import base64
        header, body = {}, []
        for name, L in doc['layers'].items():
            counts = base64.b64decode(L['counts'])
            coords = base64.b64decode(L['coords'])
            header[name] = {'polylines': len(counts) // 4, 'coords': len(coords) // 4, 'area': L['area']}
            body.append(counts)
            body.append(coords)
        h = json.dumps({'stamp': doc['stamp'], 'layers': header}).encode('utf-8')
        # padded to a four-byte boundary: the page views the counts and coordinates as
        # typed arrays straight over the body, and a Uint32Array cannot start at an odd
        # offset. The stamp is a float whose printed length varies with the file's mtime,
        # so an unpadded header was aligned by luck - and a RangeError, swallowed, left
        # the map with no land, no water and a blank thumbnail after one rebuild.
        h += b' ' * (-len(h) % 4)
        doc['_bytes'] = _pack('I', [len(h)]) + h + b''.join(body)
    return doc['_bytes']


def basemap_payload(run_dir=None):
    """The standing picture - coast, water, parkland, roads, rail, tram - from
    the RUN'S city's basemap.json, decoded from its projected packing and
    re-packed as WGS84 Float32 polylines: one array of vertex counts and one of
    lon/lat pairs per layer. Optional: the page draws the run without it. The
    run's city, never the server's: the reference city's rails were drawn under
    a Mumbai run (the user's report, 22 September 2026, 9.206)."""
    import base64
    import struct
    name = run_city(run_dir) if run_dir else _city.CITY
    # the server's city through city.path (the artefact ledger reads that call);
    # another city's by the same city-relative path under its own directory
    path = _city.path('data', 'processed', 'basemap.json')
    if name != _city.CITY:
        path = os.path.join(_city.CITIES_DIR, name, 'data', 'processed', 'basemap.json')
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return {'available': False, 'reason': 'no basemap.json - build it with '
                                              'src/analyse/build_basemap.py'}
    hit = _BASEMAP_CACHE.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    doc = _load_json(path)
    if not doc:
        return {'available': False, 'reason': 'basemap.json unreadable'}
    ox, oy = doc['origin']
    tf = _to_wgs84(run_dir)
    layers = {}
    for name, b64 in doc['layers'].items():
        raw = base64.b64decode(b64)
        i = 0
        counts, xs, ys = [], [], []
        last = None
        while i + 12 <= len(raw):
            x0, y0, n = struct.unpack_from('<iiH', raw, i)
            i += 12
            if n < 2 or i + (n - 1) * 4 > len(raw):
                break
            cont = (last == (x0, y0))
            px, py = x0, y0
            if not cont:
                counts.append(1)
                xs.append(px / 100.0 + ox)
                ys.append(py / 100.0 + oy)
            for _ in range(n - 1):
                dx, dy = struct.unpack_from('<hh', raw, i)
                i += 4
                px += dx
                py += dy
                counts[-1] += 1
                xs.append(px / 100.0 + ox)
                ys.append(py / 100.0 + oy)
            last = (px, py)
        if not xs:
            continue
        lons, lats = tf.transform(xs, ys)
        pairs = []
        for lo, la in zip(lons, lats):
            pairs += [lo, la]
        layers[name] = {'counts': _b64('I', counts), 'coords': _b64('f', pairs),
                        'area': name in ('coast', 'water', 'green', 'sand')}
    out = {'available': True, 'stamp': stamp, 'layers': layers}
    _BASEMAP_CACHE[path] = (stamp, out)
    return out


# ---------------------------------------------------------------- the server

def _page():
    """The page as it is on disk NOW. A server reads it ONCE, when it starts
    (`make_handler`), so the page it serves and the routes it answers are one
    revision: the launcher's embedded server imported the midnight routes
    (`network.json`, `basemap.json`) and, reading this file per request, served
    the 02:58 page that asks for `network.bin`, `basemap.bin` and
    `traffic.geojson` - three 404s and a map with no layers, on a port that
    cannot be restarted without killing the arm. `--reload` re-reads per request
    for editing the page against a standalone server."""
    with open(os.path.join(_HERE, 'run_view.html'), encoding='utf-8') as f:
        html = f.read()
    return (html.replace('__POLL_MS__', str(int(POLL_S * 1000)))
                .replace('__FAST_MS__', str(int(FAST_POLL_S * 1000))))


def _query(path):
    from urllib.parse import parse_qs, urlsplit
    parts = urlsplit(path)
    return parts.path, {k: v[-1] for k, v in parse_qs(parts.query).items()}


def make_handler(default_run_dir, reload_page=False):
    page_html = None if reload_page else _page()

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, body, ctype='application/json', code=200):
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', ctype + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionAbortedError):
                pass

        def _send_file(self, path, ctype='application/json'):
            if not os.path.exists(path):
                self._send('{"error":"absent"}', code=404)
                return
            try:
                with open(path, 'rb') as f:
                    self._send(f.read(), ctype)
            except OSError:
                self._send('{"error":"unreadable"}', code=503)

        def _run_dir(self, q):
            name = (q.get('run') or '').strip()
            if not name:
                return default_run_dir
            # a name, never a path: the picker offers what the store holds
            if os.sep in name or '/' in name or name.startswith('.'):
                return None
            return _results_store.resolve_records(name) or None

        def do_GET(self):
            path, q = _query(self.path)
            if path in ('/', '/index.html'):
                self._send(page_html if page_html is not None else _page(), 'text/html')
                return
            if path == '/runs.json':
                self._send(json.dumps({'default': os.path.basename(default_run_dir),
                                       'runs': list_runs()}))
                return
            run_dir = self._run_dir(q)
            if run_dir is None:
                self._send('{"error":"no such run"}', code=404)
                return
            if path in ('/thumb/default.light.png', '/thumb/default.dark.png', '/thumb/satellite.png'):
                # the map-type pictures: the run's city's own snapshots of its two views,
                # taken once and kept with its figures; a city without them shows the
                # page's drawn illustration instead (the <img> falls back on a 404)
                self._send_file(os.path.join(_city.CITIES_DIR, run_city(run_dir), 'docs', 'reference',
                                             'figures', 'viewer_' + path[7:]), 'image/png')
                return
            if path == '/basemap.bin':
                body = basemap_bytes(run_dir)
                if body is None:
                    self._send('{"error":"no basemap"}', code=404)
                else:
                    self._send(body, 'application/octet-stream')
                return
            if path == '/status.json':
                doc = scan(run_dir)
                doc['family'] = family_of_run(doc['name'])
                doc['city'] = run_city(run_dir)
                doc['server_city'] = _city.CITY
                # the per-iteration series stay in scan() for the digest; the page reads
                # neither, and they were 50 KB of every half-second poll
                doc.pop('modes', None)
                doc.pop('scores', None)
                self._send(json.dumps(doc))
            elif path == '/modes.json':
                it = q.get('it')
                self._send(json.dumps(modes(run_dir, int(it) if it else None)))
            elif path == '/summary.json':
                self._send_file(os.path.join(run_dir, '_summary.json'))
            elif path == '/network.bin':
                net = network_bytes(run_dir)
                if not net:
                    self._send('{"error":"the run network could not be read"}', code=404)
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Length', str(len(net['bytes'])))
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Network-Stamp', repr(net['stamp']))
                    self.send_header('X-Links', str(len(net['ids'])))
                    self.end_headers()
                    try:
                        self.wfile.write(net['bytes'])
                    except (BrokenPipeError, ConnectionAbortedError):
                        pass
            elif path == '/hotspot.json':
                doc = dict(hotspot(run_dir))
                doc.pop('_geojson', None)
                if q.get('meta'):        # the GL page: the window's facts without the offline host's arrays
                    for k in ('index', 'volume', 'delay'):
                        doc.pop(k, None)
                self._send(json.dumps(doc))
            elif path == '/traffic.geojson':
                doc = hotspot(run_dir)
                if not doc.get('available'):
                    self._send('{"type":"FeatureCollection","features":[]}')
                else:
                    self._send(doc['_geojson'], 'application/geo+json')
            elif path == '/routes.json':
                self._send(json.dumps(routes_summary(run_dir)))
            elif path == '/routes.geojson':
                self._send(routes_geojson(run_dir, (q.get('mode') or '').strip()), 'application/geo+json')
            elif path == '/links.json':
                self._send_file(os.path.join(run_dir, 'output', 'telemetry_links.json'))
            else:
                self._send('{"error":"not found"}', code=404)

        def log_message(self, *_args):
            pass  # the run's own log is the only one that matters

    return Handler


class _Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Loopback server that REFUSES a port already in use, one thread per
    request so a 6 MB network payload never blocks the half-second poll.

    `allow_reuse_address` must stay false on Windows. SO_REUSEADDR there lets a
    second socket bind a port that is already bound instead of failing, so the
    port scan in `serve` below silently "succeeded" on the SAME port for every
    concurrent run: three live views each printed 8731, 8732 and 8733 were never
    opened, and only the first server ever answered. On POSIX the flag only
    skips TIME_WAIT and is harmless, so it is kept there.
    """

    allow_reuse_address = (os.name != 'nt')
    daemon_threads = True


def serve(run_dir, port=None, poll_s=None, background=True, reload_page=False):
    """Bind on loopback and serve. Returns the url, or None if no port is free."""
    port = int(port or PORT)
    handler = make_handler(os.path.abspath(run_dir), reload_page=reload_page)
    httpd = None
    for candidate in range(port, port + 20):
        try:
            httpd = _Server(('127.0.0.1', candidate), handler)
            port = candidate
            break
        except OSError:
            continue
    if httpd is None:
        return None
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    url = 'http://127.0.0.1:%d/' % port
    if not background:
        try:
            t.join()
        except KeyboardInterrupt:
            httpd.shutdown()
    return url


def newest_run():
    names = sorted(_results_store.run_names())
    for name in reversed(names):
        d = _results_store.resolve_records(name)
        if d:
            return d
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', default=None,
                    help='a directory name under results/, or a path; default '
                         'the newest run the store holds (the page can switch)')
    ap.add_argument('--port', type=int, default=None)
    ap.add_argument('--once', action='store_true',
                    help='print the status json and exit, serving nothing')
    ap.add_argument('--reload', action='store_true',
                    help='re-read run_view.html on every request (editing the page); '
                         'by default the page is read once, so it and the server are one revision')
    args = ap.parse_args()

    run_dir = args.run
    if run_dir is not None and not run_dir.strip():
        # An empty --run resolved to results/ itself and served a directory that
        # is not a run, reporting "no telemetry" for a run that had plenty.
        raise SystemExit('--run is empty')
    if run_dir is None:
        run_dir = newest_run()
        if run_dir is None:
            raise SystemExit('the results store holds no run')
    elif not os.path.isdir(run_dir):
        run_dir = _resolve_run(args.run)
    if not os.path.isdir(run_dir):
        raise SystemExit('no such run: %s' % args.run)

    if args.once:
        print(json.dumps(scan(run_dir), indent=1)[:4000])
        return

    url = serve(run_dir, args.port, background=True, reload_page=args.reload)
    if url is None:
        raise SystemExit('no free loopback port')
    print('run viewer: %s' % url, flush=True)
    print('reading:    %s' % os.path.abspath(run_dir), flush=True)
    print('Ctrl-C to stop. The run is not affected either way.', flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print('\nstopped')


if __name__ == '__main__':
    main()
