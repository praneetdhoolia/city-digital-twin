"""Watch one run: its pace, its ceiling, its watchers, and the events worth a line.

    python src/run/watch_run.py --run <name>              # one line, now
    python src/run/watch_run.py --run <name> --events     # a line per event, until the end
    python src/run/watch_run.py --run <name> --events --read   # ... with each readable
                                                                 # iteration's reading

The session that monitored the routers pair (DECISIONS.md 9.176) did this by
hand: a scratch script for the pace and the ceiling projection, an inline shell
loop for the events, and a full `--trend` read at every readable iteration -
forty wake-ups, each paying the arm's own CPU. Two things it needed were not
readable anywhere: whether the HARNESS was still alive (it had died at
iteration 34, and BUSY said only that a JVM was), and where the 30.0 h ceiling
would land against the 250 horizon once the post-cutoff tail ran faster than
the innovating iterations. Both are lines here.

One line, now (`--run`): the last ENDED iteration and its seconds, the recent
median, the elapsed hours, the ceiling's remaining hours and where it lands at
the recent median and with the post-cutoff tail at its own measured pace, the
card's status, whether the harness pid and a JVM are alive, the log's age,
and whether `_run.json` exists.

Events (`--events`, polled every `--poll` seconds, default 30), one line each:

    READABLE it.N ...      a milestone's tables landed (with the reading if --read)
    HARNESS DEAD ...       the harness pid is gone while the JVM writes on (once)
    STALL? ...             the log has been silent past RUN.monitor.stall_s
    GATE STOP ...          `_gate_stop.json` appeared
    JVM GONE ...           no java process and no record yet
    ENDED ...              `_run.json` exists: its completion and reached_iteration; exit 0

Nothing here launches, stops, kills or recompiles anything; it reads. It is
meant to be the one command a Monitor runs, so that a session wakes on events
and not on a clock. The reading behind `--read` is `report_mode_ridership`'s
own, memoised under the run's `_trend/` as `--trend` is (9.176).
"""
import argparse
import csv
import datetime as dt
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

import results_store                                              # noqa: E402
from procs import card_pid_alive, arm_running                          # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

STOPWATCH = os.path.join('output', 'stopwatch.csv')


def _load(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def values(run_dir):
    """The run's own resolved registry values (its `_config.json` snapshot)."""
    doc = _load(os.path.join(run_dir, '_config.json')) or {}
    return doc.get('values') or {}


def iteration_seconds(run_dir):
    """{iteration: wall seconds} from the controller's own stopwatch."""
    path = os.path.join(run_dir, STOPWATCH)
    out = {}
    try:
        with open(path, encoding='utf-8', newline='') as fh:
            rows = list(csv.reader(fh, delimiter=';'))
    except OSError:
        return out
    if not rows:
        return out
    head = rows[0]
    try:
        b, e = head.index('BEGIN iteration'), head.index('END iteration')
    except ValueError:
        return out
    for r in rows[1:]:
        if len(r) <= max(b, e) or not r[b] or not r[e]:
            continue
        try:
            t0 = dt.datetime.strptime(r[b], '%H:%M:%S')
            t1 = dt.datetime.strptime(r[e], '%H:%M:%S')
            out[int(r[0])] = ((t1 - t0).seconds) % 86400
        except ValueError:
            continue
    return out


def readable_iterations(run_dir):
    """Iterations whose trips table exists, ascending."""
    import iteration_reading                                  # noqa: PLC0415
    return iteration_reading.iterations_with(run_dir, 'trips')


def projection(per, cfg, meta, now=None):
    """Where the ceiling lands, at the recent median and with the tail's pace.

    The innovating iterations and the post-cutoff tail run at different paces
    (arm 0: ~350 s and ~262 s; the routers pair 340-450 s and 262-320 s), so a
    single median over-states the ceiling's bite by 20-30 iterations. The tail
    pace is this run's own once it has three post-cutoff iterations; before
    that it is the innovating median, and the line says which.
    """
    now = now or time.time()
    horizon = cfg.get('RUN.controler.last_iteration') or meta.get('iterations')
    cutoff = None
    frac = cfg.get('RUN.replanning.fraction_to_disable_innovation')
    if horizon and frac:
        cutoff = int(round(horizon * frac))
    ceiling_h = cfg.get('RUN.gate.wall_ceiling_h')
    try:
        t0 = time.mktime(time.strptime(meta.get('started') or '', '%Y-%m-%dT%H:%M:%S'))
    except (TypeError, ValueError):
        t0 = None
    elapsed_h = (now - t0) / 3600 if t0 else None
    done = max(per) if per else -1
    recent = [per[i] for i in sorted(per) if i > 0][-10:]
    med = statistics.median(recent) if recent else None
    tail = [per[i] for i in sorted(per) if cutoff is not None and i > cutoff]
    tail_med = statistics.median(tail) if len(tail) >= 3 else None
    out = dict(horizon=horizon, cutoff=cutoff, ceiling_h=ceiling_h,
               elapsed_h=elapsed_h, done=done, median_s=med,
               tail_median_s=tail_med, last_s=per.get(done))
    if ceiling_h is not None and elapsed_h is not None and med:
        rem_s = max(0.0, (ceiling_h - elapsed_h) * 3600)
        out['remaining_h'] = rem_s / 3600
        out['lands_at_median'] = done + rem_s / med
        if cutoff is not None and tail_med:
            to_cut = max(0, cutoff - done) * med
            out['lands_with_tail'] = (done + rem_s / med if rem_s <= to_cut
                                      else cutoff + (rem_s - to_cut) / tail_med
                                      if done < cutoff else done + rem_s / tail_med)
    return out


def snapshot(run_dir):
    """Everything the one-line report states, as a dict."""
    meta = _load(os.path.join(run_dir, '_meta.json')) or {}
    cfg = values(run_dir)
    per = iteration_seconds(run_dir)
    proj = projection(per, cfg, meta)
    log = os.path.join(run_dir, 'matsim.log')
    try:
        log_age = time.time() - os.path.getmtime(log)
    except OSError:
        log_age = None
    progress = _load(os.path.join(run_dir, '_progress.json')) or {}
    # A run with no `_meta.json` has not STARTED, which is not the same as
    # having died: the harness subsamples the population before the JVM
    # exists - minutes at 25 % - and for that window the card, the harness pid
    # and the JVM pid are all absent. Reading an absent pid as a dead one
    # reported a healthy probe as `harness DEAD; JVM gone` seconds after its
    # launch. `None` means NOT RECORDED YET; `False` means recorded and gone.
    card_present = os.path.exists(os.path.join(run_dir, '_meta.json'))
    harness_pid = meta.get('pid')
    harness_alive = card_pid_alive(meta, 'pid') if harness_pid else None
    # THIS run's JVM by its recorded pid; any JVM over 2 GB on the host was
    # what this read before (twelfth report), which a second arm or a probe
    # would have satisfied for a dead one
    jvm_pid = meta.get('jvm_pid')
    if jvm_pid:
        jvm = card_pid_alive(meta, 'jvm_pid')
    elif card_present:
        jvm = arm_running()
    else:
        jvm = None
    rec = _load(os.path.join(run_dir, '_run.json'))
    return dict(name=os.path.basename(run_dir), status=meta.get('status'),
                card_present=card_present,
                harness_pid=harness_pid,
                harness_alive=harness_alive,
                jvm_pid=jvm_pid,
                jvm_alive=(None if jvm is None else bool(jvm)),
                log_age_s=None if log_age is None else int(log_age),
                progress_iteration=progress.get('iteration'),
                progress_written=progress.get('written_at'),
                stall_s=cfg.get('RUN.monitor.stall_s'),
                record=(None if rec is None else
                        dict(completion=rec.get('completion'),
                             reached_iteration=rec.get('reached_iteration'))),
                **proj)


def one_line(s):
    parts = ['%s' % time.strftime('%H:%M:%S'),
             'it.%s done' % s['done'] if s['done'] >= 0 else 'no iteration ended']
    if s.get('last_s') is not None:
        parts[-1] += ' (%d s)' % s['last_s']
    if s.get('record'):
        # a run with a record has ended: its clocks and its watchers are history
        parts.append('median %d s' % s['median_s'] if s.get('median_s') else 'no pace')
        parts.append('status %s' % s['status'])
        parts.append('_run.json %s at %s' % (s['record']['completion'], s['record']['reached_iteration']))
        return '; '.join(parts)
    if s.get('median_s'):
        parts.append('median %d s' % s['median_s'])
    if s.get('tail_median_s'):
        parts.append('tail %d s' % s['tail_median_s'])
    if s.get('elapsed_h') is not None:
        parts.append('elapsed %.2f h' % s['elapsed_h'])
    if s.get('remaining_h') is not None:
        land = 'ceiling in %.2f h -> ~it.%.0f at the median' % (s['remaining_h'], s['lands_at_median'])
        if s.get('lands_with_tail') is not None:
            land += ', ~it.%.0f with the tail' % s['lands_with_tail']
        land += ' (horizon %s)' % s['horizon']
        parts.append(land)
    parts.append('status %s' % s['status'])
    if not s.get('card_present'):
        parts.append('NOT STARTED YET (no _meta.json; the harness subsamples '
                     'before the JVM exists)')
    parts.append('harness %s' % ('alive' if s['harness_alive'] else
                                 'unknown' if s['harness_alive'] is None else 'DEAD'))
    parts.append('JVM %s' % ('alive' if s['jvm_alive'] else 'unknown' if s['jvm_alive'] is None else 'gone'))
    if s.get('log_age_s') is not None:
        parts.append('log %d s old' % s['log_age_s'])
    if s.get('record'):
        parts.append('_run.json %s at %s' % (s['record']['completion'], s['record']['reached_iteration']))
    else:
        parts.append('_run.json absent')
    return '; '.join(parts)


class NotWrittenYet(Exception):
    """The iteration's tables exist but MATSim has not finished writing them.

    `readable_iterations` sees a file the moment it appears, and a 25 % arm
    takes appreciable time to finish writing one: reading `trips.csv.gz` mid
    write raised `EOFError: Compressed file ended before the end-of-stream
    marker was reached` and killed the whole watch, which is the failure
    9.176 exists to prevent - a run left with nobody reporting on it. The
    iteration is left unseen and read again at the next poll.
    """


def reading_line(run_dir, it):
    """One compact line of the twelve modes at one iteration, from the memo
    where it exists (report_mode_ridership 9.176) and derived otherwise."""
    import contextlib
    import csv
    import io
    import zlib
    import report_mode_ridership as rmr
    stamp = rmr._reader_stamp()
    doc = rmr.read_memo(run_dir, it, False, stamp)
    if doc is None:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rmr.report(run_dir, it, False)
        except SystemExit as e:
            return 'reading unavailable: %s' % e
        except (EOFError, OSError, zlib.error, csv.Error) as e:
            raise NotWrittenYet('%s: %s' % (type(e).__name__, e))
        except Exception as e:      # a READING must never take the watch down
            return 'reading failed: %s: %s' % (type(e).__name__, e)
        doc = rmr.write_memo(run_dir, it, False, stamp)
    bits = []
    for m, v in doc['modelled'].items():
        t = doc['targets'].get(m)
        if v is None or not t:
            continue
        if m in ('truck', 'freight_train'):
            continue
        bits.append('%s %+.1f%%' % (m, 100.0 * (v - t) / t))
    return ' '.join(bits)


def events(run_dir, poll, read, heartbeat):
    """Print one line per event until the run has a record; exit 0 then."""
    seen = set(readable_iterations(run_dir))
    said_dead = False
    said_stall = False
    said_gate = False
    last_beat = time.time()
    while True:
        s = snapshot(run_dir)
        if s.get('record'):
            print('ENDED %s: %s at iteration %s' % (s['name'], s['record']['completion'],
                                                     s['record']['reached_iteration']), flush=True)
            return 0
        for it in readable_iterations(run_dir):
            if it in seen:
                continue
            line = 'READABLE it.%d landed; %s' % (it, one_line(s))
            if read:
                try:
                    line += '\n    ' + reading_line(run_dir, it)
                except NotWrittenYet:
                    # still being written; leave it unseen and try next poll
                    continue
            seen.add(it)
            print(line, flush=True)
        if s['harness_alive'] is False and s['jvm_alive'] and not said_dead:
            print('HARNESS DEAD %s: pid %s is gone while the JVM writes on (log %s s old): '
                  'no ceiling, stall or gate watcher runs and nothing will write the record. '
                  'run.py --stop now, or run.py --close-out once it reaches its horizon.'
                  % (s['name'], s['harness_pid'], s['log_age_s']), flush=True)
            said_dead = True
        stall_s = s.get('stall_s') or 300
        if s['log_age_s'] is not None and s['log_age_s'] > stall_s and s['jvm_alive']:
            if not said_stall:
                print('STALL? %s: matsim.log silent %d s (RUN.monitor.stall_s %s) at it.%s'
                      % (s['name'], s['log_age_s'], stall_s, s['done']), flush=True)
                said_stall = True
        else:
            said_stall = False
        if os.path.exists(os.path.join(run_dir, '_gate_stop.json')) and not said_gate:
            print('GATE STOP %s: %s' % (s['name'], json.dumps(_load(os.path.join(run_dir, '_gate_stop.json')))[:300]),
                  flush=True)
            said_gate = True
        if s['jvm_alive'] is False and s['harness_alive'] is False:
            print('JVM GONE %s: no java process and no _run.json (status %s); if the log ends in a clean '
                  'shutdown at the horizon, run.py --close-out; otherwise reconcile records it at the next launch'
                  % (s['name'], s['status']), flush=True)
            time.sleep(max(poll, 60))
        if heartbeat and time.time() - last_beat >= heartbeat:
            print('HEARTBEAT ' + one_line(s), flush=True)
            last_beat = time.time()
        time.sleep(poll)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--run', required=True, help='a run name or directory')
    ap.add_argument('--events', action='store_true',
                    help='print a line per event until the run has a record')
    ap.add_argument('--read', action='store_true',
                    help='with --events: print each readable iteration\'s twelve-mode deviations')
    ap.add_argument('--poll', type=float, default=30.0, help='seconds between polls (default 30)')
    ap.add_argument('--heartbeat', type=float, default=0.0,
                    help='with --events: also print the one-line state every N seconds (default: never)')
    ap.add_argument('--json', action='store_true', help='print the snapshot as JSON instead of one line')
    a = ap.parse_args()
    run_dir = results_store.resolve(a.run)
    if run_dir is None:
        raise SystemExit('no run named %s' % a.run)
    if a.events:
        return events(run_dir, a.poll, a.read, a.heartbeat)
    s = snapshot(run_dir)
    print(json.dumps(s, indent=1) if a.json else one_line(s))
    return 0


if __name__ == '__main__':
    sys.exit(main())
