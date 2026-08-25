#!/usr/bin/env python
"""A machine-readable per-iteration digest of a run in flight (issue #76).

Monitoring a ~65 h arm used to mean reading `matsim.log` or the human-facing
live view. This writes one compact `_progress.json` into the run directory,
refreshed as iterations complete, so an agent or a script reads one file:

  * per-mode shares from `modestats.csv` - EVERY mode individually, never an
    aggregate row (standing directive, NEXT_AGENT_BRIEF 0.3);
  * the drift trajectory against the declared `RUN.relaxation.drift_tolerance_pp`
    (delegated to `summarise_run.relaxation`, the single implementation of that
    verdict);
  * s/iteration pace against the declared `RUN.monitor.pace_band_s` - which
    mechanises the conditional-replication rule (DECISIONS.md 9.72: arm B
    launches only if arm A's solo iterations 2-5 pace inside the closed
    family's band);
  * ETA to `lastIteration` and a stall flag per `RUN.monitor.stall_s`.

**This is an OBSERVER** (the telemetry isolation rule, DECISIONS.md 9.36): it
runs on a daemon thread in the harness process, reads the run directory, and is
structurally unable to touch the mobsim. Every failure is swallowed and
reported on the next successful write (`write_failures`), because a run that
dies of its own instrumentation is worse than a run without instrumentation.
The file is replaced atomically with a bounded retry, the same discipline
`RunTelemetry.java` earned on Windows.

    python src/analyse/progress_digest.py --run results/<run> --once
"""
import argparse
import json
import os
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, _HERE)
import run_view  # noqa: E402
from registry import outputs  # noqa: E402

PROGRESS = '_progress.json'
REPLACE_ATTEMPTS = 5
REPLACE_BACKOFF_S = 0.05


def solo_check_iterations(cfg=None):
    """The solo iterations the 9.72 conditional-replication rule reads,
    from the declared RUN.monitor.solo_check_iterations window."""
    if cfg is None:
        import registry as _registry
        cfg = _registry.load()
    lo, hi = cfg.get('RUN.monitor.solo_check_iterations')
    return tuple(range(int(lo), int(hi) + 1))


def _iteration_durations(log):
    """{iteration: wall seconds} from the controller's own BEGIN markers."""
    iters = run_view.read_iterations(log)
    out = {}
    for (n0, t0), (n1, t1) in zip(iters, iters[1:]):
        if n1 == n0 + 1:
            out[n0] = round(t1 - t0, 2)
    return out


def digest(run_dir, band=None, solo_iters=None):
    """The one-file status of a run: scan() plus the declared pace band."""
    solo_iters = solo_iters or solo_check_iterations()
    scan = run_view.scan(run_dir)
    modes = scan.get('modes') or {}
    mode_share_last = {}
    for col, series in modes.items():
        if col == 'iteration' or not series:
            continue
        mode_share_last[col] = series[-1]

    durations = _iteration_durations(os.path.join(run_dir, 'matsim.log'))
    pace = dict(median_s=scan.get('median_iteration_s'),
                last_s=scan.get('last_iteration_s'),
                band_s=list(band) if band else None,
                median_in_band=None, last_in_band=None,
                solo_iterations_s={str(n): durations.get(n)
                                   for n in solo_iters},
                solo_in_band=None)
    if band:
        lo, hi = float(band[0]), float(band[1])
        if pace['median_s'] is not None:
            pace['median_in_band'] = lo <= pace['median_s'] <= hi
        if pace['last_s'] is not None:
            pace['last_in_band'] = lo <= pace['last_s'] <= hi
        solo = [durations.get(n) for n in solo_iters]
        if all(s is not None for s in solo):
            pace['solo_in_band'] = all(lo <= s <= hi for s in solo)

    try:
        meta = json.load(open(os.path.join(run_dir, '_meta.json'),
                              encoding='utf-8'))
    except (OSError, ValueError):
        meta = None

    return {
        'written_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'name': scan.get('name'),
        'state': scan.get('state'),
        'stalled': scan.get('state') == 'stalled',
        'scenario': scan.get('scenario'),
        'day': scan.get('day'),
        'fraction': scan.get('fraction'),
        'seed': scan.get('seed'),
        'iteration': scan.get('iteration'),
        'target': scan.get('target'),
        'remaining': scan.get('remaining'),
        'eta_s': scan.get('eta_s'),
        'elapsed_s': scan.get('elapsed_s'),
        'innovation_off_at': scan.get('innovation_off_at'),
        'log_age_s': scan.get('log_age_s'),
        'mode_share_last_iteration': mode_share_last,
        'relaxation': scan.get('relaxation'),
        'pace': pace,
        'warm_started_from': (meta or {}).get('warm_started_from'),
        'rc': scan.get('rc'),
    }


def _write_atomic(path, doc):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write('\n')
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(tmp, path)
            return True
        except OSError:
            time.sleep(REPLACE_BACKOFF_S * (attempt + 1))
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False


def write_once(run_dir, band=None, solo_iters=None):
    """One digest write. Validated against its declared contract; a document
    that fails the contract is a defect and IS raised here (the CLI path).
    The harness loop below never lets that reach the run."""
    doc = digest(run_dir, band=band, solo_iters=solo_iters)
    problems = outputs.validate_doc('progress', doc)
    if problems:
        raise outputs.OutputError('digest does not meet its contract:\n  %s'
                                  % '\n  '.join(problems))
    _write_atomic(os.path.join(run_dir, PROGRESS), doc)
    return doc


def capture_machine_context(run_dir, since_epoch_s):
    """Snapshot the machine-level suspects when a stall begins (issue #66).

    The 22 Aug recurrence hit BOTH concurrent arms at the same wall-clock
    time while they were in different iterations, which excludes any cause
    inside MATSim; the named candidates are OS scheduled maintenance,
    antivirus scanning and memory-standby trimming. The issue's own
    settlement condition is "correlate the event window with Windows Task
    Scheduler / Defender scan history the next time it fires" - so the
    observer captures exactly that window, bounded by the daemon's OWN last
    healthy observation (no invented lookback constant). Instrumentation
    only: never raises, never touches the mobsim, wall-clock timestamps are
    legitimate here because the artefact records the MACHINE, not the model.
    """
    if os.name != 'nt':
        return None
    import subprocess
    start = time.strftime('%Y-%m-%dT%H:%M:%S',
                          time.localtime(since_epoch_s))
    out = {'captured_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
           'window_start': start, 'logs': {}}
    for name, log in (('defender',
                       'Microsoft-Windows-Windows Defender/Operational'),
                      ('task_scheduler',
                       'Microsoft-Windows-TaskScheduler/Operational')):
        cmd = ("Get-WinEvent -FilterHashtable @{LogName='%s';"
               "StartTime=[datetime]'%s'} -ErrorAction Stop | "
               "Select-Object -First 200 TimeCreated, Id, "
               "@{n='Message';e={$_.Message.Substring(0, "
               "[Math]::Min(300, $_.Message.Length))}} | ConvertTo-Json"
               % (log, start))
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-Command', cmd],
                               capture_output=True, text=True, timeout=60)
            out['logs'][name] = (json.loads(r.stdout) if r.returncode == 0
                                 and r.stdout.strip() else
                                 {'error': (r.stderr or 'no events').strip()
                                  [:500]})
        except Exception as e:                               # noqa: BLE001
            out['logs'][name] = {'error': str(e)[:500]}
    path = os.path.join(run_dir, '_machine_context_%s.json'
                        % time.strftime('%Y%m%dT%H%M%S'))
    try:
        _write_atomic(path, out)
    except Exception:                                        # noqa: BLE001
        return None
    return path


def serve(run_dir, interval_s, band=None, solo_iters=None, background=True):
    """Refresh `_progress.json` on a daemon thread until the run finishes.

    Never raises past this frame: the digest is instrumentation, and the
    telemetry isolation rule (9.36) applies to it exactly as to the live view.
    Failures are counted and surfaced inside the next successful write.
    """
    failures = {'n': 0, 'last': None}
    solo_iters = solo_iters or solo_check_iterations()

    def loop():
        last_healthy_wall = time.time()
        was_stalled = False
        while True:
            try:
                doc = digest(run_dir, band=band, solo_iters=solo_iters)
                if failures['n']:
                    doc['write_failures'] = dict(failures)
                # issue #66: on the transition INTO a stall, capture the
                # Defender / Task Scheduler history for exactly the window
                # since the daemon's last healthy observation
                stalled = bool(doc.get('stalled'))
                if stalled and not was_stalled:
                    doc['machine_context'] = capture_machine_context(
                        run_dir, last_healthy_wall)
                if not stalled:
                    last_healthy_wall = time.time()
                was_stalled = stalled
                if not _write_atomic(os.path.join(run_dir, PROGRESS), doc):
                    failures['n'] += 1
                    failures['last'] = 'atomic replace lost to a directory lock'
                if doc.get('state') in ('finished', 'failed'):
                    return
            except Exception as e:                           # noqa: BLE001
                failures['n'] += 1
                failures['last'] = str(e)
            time.sleep(interval_s)

    t = threading.Thread(target=loop, name='progress-digest', daemon=True)
    t.start()
    if not background:
        t.join()
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', required=True)
    ap.add_argument('--once', action='store_true',
                    help='write one digest and exit (default: loop)')
    ap.add_argument('--interval', type=float, default=None,
                    help='seconds between refreshes; default '
                         'RUN.monitor.progress_interval_s')
    a = ap.parse_args()
    import registry as _registry
    cfg = _registry.load()
    band = cfg.get('RUN.monitor.pace_band_s')
    solo = solo_check_iterations(cfg)
    interval = a.interval or cfg.get('RUN.monitor.progress_interval_s')
    if a.once:
        doc = write_once(a.run, band=band, solo_iters=solo)
        print(json.dumps(doc, indent=2))
        return 0
    serve(a.run, interval, band=band, solo_iters=solo, background=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
