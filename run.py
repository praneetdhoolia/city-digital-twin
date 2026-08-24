#!/usr/bin/env python
"""Run a scenario. The one command this repository needs a newcomer to know.

    python run.py                            the default run: S2, weekday, 25%, 1000 iterations
    python run.py --run-config smoke         a plumbing test: 1%, 2 iterations
    python run.py --list                     what can be run: scenarios, day types, overlays
    python run.py --dry-run                  resolve every input and print it; execute nothing
    python run.py --run-config ride_fix_10pct        a committed run overlay
    python run.py --scenario S3 --day SAT --fraction 0.10 --iterations 1000

The run directory is named by the runner, never by the caller:
`results/<launch yyyymmddThhmmss>_<iterations>it_<sample pct>pct`.

This is a front door, not a second harness. Everything below it is
`src/run/run_matsim.py`, which owns the run identity, the subsample, the config
emission and the run record; this module adds argument defaults, a dry run, a
listing and the metric extraction that would otherwise be a second command.

**It still does not invent an iteration count.** `RUN.controler.last_iteration`
is declared `unobtained` in the registry (DECISIONS.md 9.7: 100 and 250 are
both MEASURED to be too low, and no justified value has been established), so a
bare `python run.py` does not quietly pick one in code. It selects the
committed `default_25pct` overlay - 25% sample, 1000 iterations, the 9.7
working horizon - which names its sweep member and its provenance like any
other overlay, and the banner below says exactly what was chosen and why it is
provisional (issue #5). Expect ~16 hours of wall clock.

**Nothing this produces is a result** until the model has a calibrated base;
see docs/STATUS.md.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ('run', 'analyse', 'registry', ''):
    sys.path.insert(0, os.path.join(HERE, 'src', sub) if sub else os.path.join(HERE, 'src'))

import city                          # noqa: E402
import registry                      # noqa: E402
import run_matsim                    # noqa: E402

DEFAULT_OVERLAY = 'default_25pct'

DEFAULT_BANNER = """
+---------------------------------------------------------------------------+
|  DEFAULT RUN - the committed `default_25pct` overlay.                      |
|                                                                            |
|  No overlay and no --iterations were given, so this runs S2 x WEEKDAY at   |
|  a 25% sample for 1000 iterations (the DECISIONS.md 9.7 working horizon).  |
|  Expect roughly 16 HOURS of wall clock and a ~40 GiB heap. Run ONE large   |
|  run at a time - concurrent arms paged this machine once already.          |
|                                                                            |
|  The iteration count is PROVISIONAL: RUN.controler.last_iteration is       |
|  unobtained, and issue #5 re-measures relaxation on the rebuilt inputs.    |
|  NOTHING THIS PRODUCES IS A RESULT until the model has a calibrated base.  |
|                                                                            |
|  For a quick plumbing test instead:  python run.py --run-config smoke      |
+---------------------------------------------------------------------------+
"""


def listing():
    """What is actually runnable, read from the package rather than hardcoded."""
    print('scenarios with assembled run inputs (%s):' % run_matsim.SETS)
    if os.path.isdir(run_matsim.SETS):
        for s in sorted(os.listdir(run_matsim.SETS)):
            if not os.path.isdir(os.path.join(run_matsim.SETS, s)):
                continue                       # the run-inputs report sits alongside
            days = sorted(d for d in os.listdir(os.path.join(run_matsim.SETS, s))
                          if os.path.isdir(os.path.join(run_matsim.SETS, s, d)))
            print('  %-5s %s' % (s, ' '.join(days) if days else '(no day types)'))
    else:
        print('  none - %s does not exist' % run_matsim.SETS)

    print('\nrun overlays (--run-config):')
    runs_dir = registry.OVERLAY_DIRS['run']
    for f in sorted(os.listdir(runs_dir)) if os.path.isdir(runs_dir) else []:
        if not f.endswith('.json'):
            continue
        import json
        doc = json.load(open(os.path.join(runs_dir, f), encoding='utf-8'))
        sets = doc.get('set', {})
        print('  %-28s f=%-6s i=%-6s %s'
              % (f[:-5],
                 sets.get('RUN.sample.fraction', '-'),
                 sets.get('RUN.controler.last_iteration', '-'),
                 (doc.get('description', '')[:60] + '...')
                 if len(doc.get('description', '')) > 60 else doc.get('description', '')))

    print('\nfinished runs in %s:' % run_matsim.RESULTS)
    if os.path.isdir(run_matsim.RESULTS):
        for d in sorted(os.listdir(run_matsim.RESULTS)):
            done = os.path.exists(os.path.join(run_matsim.RESULTS, d, '_run.json'))
            print('  %-40s %s' % (d, 'complete' if done else 'incomplete'))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # The scenario default and day-type vocabulary are the CITY's, not the
    # framework's: another city declares its own in city.json, and a CLI that
    # hardwired S2/WEEKDAY rejected that city's own declared inputs.
    base_scenario = city.descriptor()['intervention']['base_scenario']
    day_types = list(city.descriptor()['day_types'])
    ap.add_argument('--scenario', default=base_scenario,
                    help='default: %s (city.json intervention.base_scenario)'
                         % base_scenario)
    ap.add_argument('--day', default=day_types[0], choices=day_types)
    ap.add_argument('--run-config', metavar='TAG',
                    help='a committed overlay under the city overlays/runs directory - '
                         'the reproducible way to vary a run. Defaults to `%s` ONLY '
                         'when no --iterations is given' % DEFAULT_OVERLAY)
    ap.add_argument('--fraction', type=float, help='sample fraction, e.g. 0.10')
    ap.add_argument('--iterations', type=int,
                    help='MATSim last iteration. There is no default: the registry '
                         'declares this field unobtained and refuses to invent one')
    ap.add_argument('--threads', type=int)
    ap.add_argument('--xmx', help='JVM heap, e.g. 26g')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--force', action='store_true',
                    help='re-run even if a complete run record already exists. The '
                         'runner names every run directory itself '
                         '(<launch>_<iterations>it_<pct>pct); a forced re-run gets '
                         'a fresh directory, nothing is overwritten')
    ap.add_argument('--warm-start', metavar='DEAD_RUN_DIR',
                    help='continue a crashed run from its newest written plans '
                         'checkpoint. Starts a NEW runner-named run; the link is '
                         'recorded as warm_started_from (issue #75, DECISIONS.md '
                         '9.76 states the validity caveat)')
    ap.add_argument('--detach', action='store_true',
                    help='launch the run under the Windows Task Scheduler so its '
                         'lifetime is independent of this shell (issue #70: '
                         'session-spawned runs died with their launching '
                         'context). Prints the run poll command and returns '
                         'immediately')
    ap.add_argument('--config-set', action='append', default=[], metavar='KEY=VALUE',
                    help='registry override, checked against the declared sweep')
    ap.add_argument('--set', action='append', default=[], metavar='KEY=VALUE',
                    help='MATSim config override, e.g. ride.constant=-3.4')
    ap.add_argument('--dry-run', action='store_true',
                    help='resolve the registry, print the snapshot, execute nothing')
    ap.add_argument('--list', action='store_true',
                    help='list runnable scenarios, run overlays and finished runs')
    ap.add_argument('--no-metrics', action='store_true',
                    help='skip metric extraction after a successful run')
    a = ap.parse_args()

    if a.list:
        return listing()

    # The one defaulting decision this script makes, and it is made loudly.
    run_config = a.run_config
    defaulted = False
    if run_config is None and a.iterations is None:
        run_config = DEFAULT_OVERLAY
        defaulted = True
        print(DEFAULT_BANNER)

    if a.detach:
        return _detach()

    overrides = registry.parse_set(a.config_set)
    for flag, key in (('fraction', 'RUN.sample.fraction'),
                      ('iterations', 'RUN.controler.last_iteration'),
                      ('threads', 'RUN.machine.threads'),
                      ('xmx', 'RUN.machine.xmx'),
                      ('seed', 'RUN.machine.seed')):
        value = getattr(a, flag)
        if value is not None:
            overrides[key] = value

    warm = None
    if a.warm_start:
        warm = run_matsim.resolve_warm_start(a.warm_start)
        overrides['RUN.controler.first_iteration'] = warm['iteration']

    cfg = run_matsim.resolve(a.scenario, a.day, run_config, overrides)

    if a.dry_run:
        print('scenario %s  day %s  overlay %s'
              % (a.scenario, a.day, run_config or '(none)'))
        src_dir = os.path.join(run_matsim.SETS, a.scenario, a.day)
        print('inputs   %s  %s' % (src_dir, 'OK' if os.path.isdir(src_dir) else 'MISSING'))
        snap = cfg.snapshot()
        values, origin = snap['values'], snap['resolved_from']
        print('\nresolved registry - %d fields, layers %s:'
              % (snap['registry_fields'], ' -> '.join(snap['layers'])))
        for key in sorted(values):
            print('  %-46s %-24s [%s]'
                  % (key, repr(values[key])[:24], origin.get(key, '?')))
        print('\ndry run: nothing was executed')
        return 0

    doc = run_matsim.run(a.scenario, a.day, cfg,
                         dict(run_matsim.parse_override(s) for s in a.set),
                         a.force, warm=warm)
    if doc.get('rc') != 0:
        return 1

    run_dir = os.path.join(run_matsim.RESULTS, doc['name'])
    if not a.no_metrics:
        try:
            _extract(run_dir)
        except Exception as e:                               # noqa: BLE001
            # A failed extraction does not invalidate the run: the run record and
            # the summary are already written, and metrics can be re-extracted.
            print('metric extraction failed (the run itself is intact): %s' % e,
                  flush=True)

    print('\nrun directory: %s' % run_dir)
    print('live/replay view:  python src/analyse/run_view.py --run %s' % run_dir)
    if defaulted:
        print('\nreminder: this ran under the default_25pct overlay. Its '
              'iteration count is provisional (issue #5), and nothing is a '
              'result until the model has a calibrated base.')
    return 0


def _extract(run_dir):
    """Shell out to the metric extractor, which owns its own CLI contract."""
    import subprocess
    subprocess.check_call([sys.executable,
                           os.path.join(HERE, 'src', 'analyse', 'extract_metrics.py'),
                           '--run', run_dir])


def _detach():
    """Launch this same invocation under the Task Scheduler and return (#70).

    Two session-spawned launches of the 4.6.9 arm died silently within minutes
    of launch, both times taking the whole process tree with them and leaving
    no error artefact (DECISIONS.md 9.72). The suspected mechanism is the
    launching context reaping its children when it ends. A Task Scheduler
    one-shot job runs under the user's account in a process tree the scheduler
    owns, so the run's lifetime is provably independent of this shell.

    A detached launch is REGISTERED here and VERIFIED only by the run itself:
    per issue #70, the launch counts as working only once `matsim.log` has
    progressed past `PersonPrepareForSim` into iterations with this launching
    context gone. This function prints exactly what to watch.
    """
    import subprocess
    import time
    if os.name != 'nt':
        raise SystemExit('--detach uses the Windows Task Scheduler; on this '
                         'platform use nohup/setsid instead.')
    stamp = time.strftime('%Y%m%dT%H%M%S')
    task = 'citysim_run_%s' % stamp
    launch_dir = os.path.join(HERE, 'results', '_launch')
    os.makedirs(launch_dir, exist_ok=True)
    log = os.path.join(launch_dir, '%s.log' % task)
    wrapper = os.path.join(launch_dir, '%s.cmd' % task)

    args = [x for x in sys.argv[1:] if x != '--detach']
    quoted = ' '.join('"%s"' % x if (' ' in x or not x) else x for x in args)
    with open(wrapper, 'w', encoding='ascii', newline='\r\n') as f:
        f.write('@echo off\r\n')
        f.write('cd /d "%s"\r\n' % HERE)
        f.write('"%s" run.py %s > "%s" 2>&1\r\n' % (sys.executable, quoted, log))
        # the task deletes itself once the run ends, so a finished launch
        # leaves no scheduled-task residue behind
        f.write('schtasks /delete /tn %s /f >nul 2>&1\r\n' % task)

    # /sc once needs a start time; it is a fallback only - /run fires it now.
    st = time.strftime('%H:%M', time.localtime(time.time() + 120))
    subprocess.check_call(['schtasks', '/create', '/tn', task,
                           '/tr', '"%s"' % wrapper, '/sc', 'once', '/st', st,
                           '/f'])
    subprocess.check_call(['schtasks', '/run', '/tn', task])
    print('\ndetached launch registered and started as scheduled task %s' % task)
    print('launcher log: %s' % log)
    print('the run directory will appear under results/ named by the runner.')
    print('VERIFY per issue #70: matsim.log must progress past '
          'PersonPrepareForSim into iterations after this shell is closed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
