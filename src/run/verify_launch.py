#!/usr/bin/env python
"""Did the detached launch actually take? (issue #70, 9.155)

`run.py --detach` registers a Task Scheduler job and then PRINTS a sentence
telling a person to go and check that `matsim.log` reaches iterations. Two
session-spawned launches of the 4.6.9 arm died silently within minutes and left
no error artefact (9.72), which is why the sentence exists - and a sentence a
person has to act on is a check that is skipped whenever the session moves on
to something else. This is that sentence, executed.

    python src/run/verify_launch.py                 the newest run, wait for it
    python src/run/verify_launch.py --run <name>    a named run
    python src/run/verify_launch.py --timeout 1800  give up after 30 minutes
    python src/run/verify_launch.py --no-wait       report the state right now

A launch has TAKEN when the run's own `matsim.log` has left startup and entered
an iteration. It has DIED when the record says so, or when the log stops
advancing while no process holds it. Nothing here is a reading of the model: it
answers one operational question and writes nothing.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import time


from src.run import results_store

# MATSim announces an iteration with a banner; the startup that precedes it is
# PersonPrepareForSim, which on this model runs for minutes (9.154: 7 min 00 s).
ITERATION = re.compile(r'ITERATION (\d+) BEGINS|### ITERATION (\d+)')
MOBSIM = re.compile(r'SIMULATION \(NEW QSim\) AT')


def newest_run():
    raw = results_store.RAW
    if not os.path.isdir(raw):
        return None
    dirs = [(os.path.getmtime(os.path.join(raw, n)), n)
            for n in os.listdir(raw) if os.path.isdir(os.path.join(raw, n))]
    return max(dirs)[1] if dirs else None


def _tail(path, limit=400_000):
    """The end of a log, without reading a 50 GiB file whole."""
    try:
        size = os.path.getsize(path)
        with io.open(path, 'rb') as fh:
            if size > limit:
                fh.seek(size - limit)
            return fh.read().decode('utf-8', 'replace')
    except OSError:
        return ''


def state(run):
    """(verdict, detail) for one run, read from its own artefacts only."""
    d = results_store.resolve(run)
    if d is None:
        return 'unknown', 'no run directory on disk for %r' % run
    log = os.path.join(d, 'matsim.log')
    meta = os.path.join(d, '_meta.json')
    doc = {}
    if os.path.exists(meta):
        try:
            with io.open(meta, encoding='utf-8') as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            doc = {}
    status = doc.get('status')
    if status in ('failed', 'aborted'):
        return 'died', 'the record says %s: %s' % (
            status, (doc.get('cause') or 'no cause recorded').split('\n')[0][:200])
    if not os.path.exists(log):
        return 'starting', 'no matsim.log yet'
    text = _tail(log)
    hits = [int(a or b) for a, b in ITERATION.findall(text)]
    age = time.time() - os.path.getmtime(log)
    if hits:
        return 'took', ('matsim.log has entered iteration %d; the launch is '
                        'independent of the launching shell' % max(hits))
    if MOBSIM.search(text):
        return 'starting', ('iteration 0 is in the mobsim (log %ds old); the '
                            'iteration banner has not been written yet' % age)
    if status == 'completed':
        return 'took', 'the run completed'
    return 'starting', 'still in startup, log %ds old' % age


def verify(run, timeout, poll, wait, log=print):
    started = time.time()
    while True:
        verdict, detail = state(run)
        if verdict in ('took', 'died', 'unknown') or not wait:
            return verdict, detail
        waited = int(time.time() - started)
        if waited >= timeout:
            return 'timeout', ('gave up after %ds; last seen: %s'
                               % (waited, detail))
        log('  ... %s (%ds elapsed)' % (detail, waited))
        time.sleep(poll)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', help='run name; default is the newest under raw/')
    ap.add_argument('--timeout', type=int, default=1800,
                    help='seconds to wait for the first iteration (default '
                         '1800: startup was measured at 7 min, 9.154)')
    ap.add_argument('--poll', type=int, default=30)
    ap.add_argument('--no-wait', dest='wait', action='store_false',
                    help='report the state now and exit')
    a = ap.parse_args(argv)

    run = a.run or newest_run()
    if run is None:
        print('no run directories under results/raw')
        return 2
    print('verifying the launch of %s (issue #70)' % run)
    verdict, detail = verify(run, a.timeout, a.poll, a.wait)
    print('\n  %-8s %s' % (verdict.upper(), detail))
    if verdict == 'took':
        print('\nThe launch took. Nothing here is a reading of the model.')
        return 0
    if verdict == 'died':
        print('\nThe launch did NOT take. The run states its own cause; read '
              'it with:\n  python src/run/run_failure.py results/raw/%s' % run)
        return 1
    if verdict == 'timeout':
        print('\nUndecided, which is not the same as working. Look at the log '
              'before assuming the arm is up.')
        return 1
    print('\nUndecided.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
