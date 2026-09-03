"""The runner's gate watcher stops a run on a BREACH and only on a breach (#112).

The watcher (`src/run/run_matsim.py:start_gate_watch`) runs the mode reporter
at every gate milestone. The reporter prints a `GATE:` line on a pass as well
as on a breach, and the watcher once keyed its stop on that substring: the
first arm to clear its iteration-100 bar would have been killed at the
milestone and recorded as aborted, indistinguishable in the record from a
breach. The watcher now reads the reporter's verdict file. This check drives
the watcher against three canned reporters - one that breaches, one that
passes, one that prints the line but writes no verdict (an older reporter) -
with a fake JVM, and asserts the JVM is killed in exactly the first case.

Stdlib only, sub-second, no run and no package: CI runs it beside the
byte-compile. Exit 1 on any failure.
"""
import io
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
for sub in ('run', 'analyse', 'registry', ''):
    sys.path.insert(0, os.path.join(REPO, 'src', sub) if sub
                    else os.path.join(REPO, 'src'))
import run_matsim  # noqa: E402

FAILS = []


def check(cond, msg):
    print(('PASS  ' if cond else 'FAIL  ') + msg)
    if not cond:
        FAILS.append(msg)


# Three canned reporters. Each accepts the watcher's exact arguments and prints
# what the real one prints at the end of its table; only the verdict differs.
BREACH = r'''
import argparse, json
ap = argparse.ArgumentParser()
ap.add_argument('--run'); ap.add_argument('--it', type=int)
ap.add_argument('--gate-json')
a = ap.parse_args()
print('| 1 | car | 70.0 | 58.3 | +20.1% | STOP >=20% | share |')
print('\nGATE: 2 mode(s) at or past 20% deviation - the standing directive '
      'is to STOP the run and fix the cause from the root:')
print('   car            modelled  70.0000  target  58.3000  +20.1%')
print('   bike           modelled   4.6000  target   2.2000  +109.1%')
json.dump(dict(run='fake', iteration=a.it, stop_deviation_pct=20.0,
               passed=False,
               breaches=[dict(mode='bike', modelled=4.6, target=2.2,
                              deviation_pct=109.1),
                         dict(mode='car', modelled=70.0, target=58.3,
                              deviation_pct=20.1)]),
          open(a.gate_json, 'w'), indent=1)
'''

PASS = r'''
import argparse, json
ap = argparse.ArgumentParser()
ap.add_argument('--run'); ap.add_argument('--it', type=int)
ap.add_argument('--gate-json')
a = ap.parse_args()
print('| 1 | car | 60.0 | 58.3 | +2.9% | ok | share |')
print('\nGATE: no mode at or past 20% deviation.')
json.dump(dict(run='fake', iteration=a.it, stop_deviation_pct=20.0,
               passed=True, breaches=[]),
          open(a.gate_json, 'w'), indent=1)
'''

# an older reporter: prints the pass line, knows no --gate-json
NO_VERDICT = r'''
import argparse
ap = argparse.ArgumentParser()
ap.add_argument('--run'); ap.add_argument('--it', type=int)
ap.add_argument('--gate-json')
a = ap.parse_args()
print('\nGATE: no mode at or past 20% deviation.')
'''


class FakeCfg(object):
    def get(self, key):
        return {'RUN.gate.interval_iterations': 100}[key]


class FakeProc(object):
    """A JVM that stays alive for `alive_polls` polls unless killed."""

    def __init__(self, alive_polls=8):
        self.alive_polls = alive_polls
        self.polls = 0
        self.killed = False

    def poll(self):
        if self.killed:
            return -9
        self.polls += 1
        return None if self.polls <= self.alive_polls else 0

    def kill(self):
        self.killed = True


class FakeTime(object):
    """No 30 s waits: the loop spins, the fake JVM ends it."""
    sleep = staticmethod(lambda s: None)
    strftime = staticmethod(time.strftime)
    time = staticmethod(time.time)


def drive(reporter_src, label):
    tmp = tempfile.mkdtemp(prefix='gate_watch_')
    reporter = os.path.join(tmp, 'reporter.py')
    with io.open(reporter, 'w', encoding='utf-8') as fh:
        fh.write(reporter_src)
    run_dir = os.path.join(tmp, 'run')
    os.makedirs(run_dir)
    saved = (run_matsim.REPORTER, run_matsim.time,
             run_matsim._last_ended_iteration)
    run_matsim.REPORTER = reporter
    run_matsim.time = FakeTime
    run_matsim._last_ended_iteration = lambda d: 100
    proc = FakeProc()
    try:
        t = run_matsim.start_gate_watch(run_dir, FakeCfg(), proc)
        check(t is not None, '%s: the watcher armed' % label)
        t.join(timeout=120)
        check(not t.is_alive(), '%s: the watcher loop ended' % label)
    finally:
        (run_matsim.REPORTER, run_matsim.time,
         run_matsim._last_ended_iteration) = saved
    stop = os.path.join(run_dir, run_matsim.GATE_STOP)
    return proc, stop


proc, stop = drive(BREACH, 'breach')
check(proc.killed, 'breach: the JVM was killed at the milestone')
check(os.path.exists(stop), 'breach: _gate_stop.json was written')
if os.path.exists(stop):
    doc = json.load(open(stop, encoding='utf-8'))
    check(doc.get('iteration') == 100, 'breach: the verdict names iteration 100')
    check([b['mode'] for b in doc.get('breaches', [])] == ['bike', 'car'],
          'breach: the verdict carries the breaching modes, largest first')
    check(doc.get('gate') and doc['gate'][0].startswith('GATE: 2 mode(s)'),
          'breach: the printed gate table is kept as the cause text')

proc, stop = drive(PASS, 'pass')
check(not proc.killed, 'pass: the JVM was NOT killed on a passing gate')
check(not os.path.exists(stop), 'pass: no _gate_stop.json on a passing gate')
check(proc.polls > 1, 'pass: the run continued past the milestone')

proc, stop = drive(NO_VERDICT, 'no verdict')
check(not proc.killed, 'no verdict: a reporter that wrote no verdict stops nothing')
check(not os.path.exists(stop), 'no verdict: no _gate_stop.json without a verdict')

if FAILS:
    print('\n%d check(s) failed' % len(FAILS))
    sys.exit(1)
print('\nALL CHECKS PASSED')
