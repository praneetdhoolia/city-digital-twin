#!/usr/bin/env python
"""Run one assembled scenario x day type, deterministically and resumably.

Takes a set out of `scenarios/matsim/<S>/<DAY>/` and runs it at a sample
fraction, writing everything derived into the run directory so the committed
inputs are never modified in place. A run is identified by its own parameters,
so re-invoking with the same ones is a no-op rather than a repeat.

**The RUNNER names the run directory** (owner directive, 24 Aug 2026):
`<launch yyyymmddThhmmss>_<iterations>it_<sample percentage>pct`, e.g.
`20260821T220310_1000it_25pct`. Nobody passes a name in. The launch stamp is
a LABEL, not identity: identity stays the parameter set recorded in
`_run.json`, which is what resume detection matches on — so the wall clock in
the name cannot make two runs of the same parameters different results.

**Resumable, not restartable.** MATSim has no mid-run checkpoint, so "resume"
here means: a completed run is detected and skipped. A run that died leaves no
`_run.json` and is repeated from the start.

**Deterministic.** One seed, fixed thread count recorded in the run record
(MATSim's mobsim partitions by thread count, so it is part of the run's
identity, not a performance knob), and a nested hash-based subsample.

**It cannot read a validation target.** This module opens the scenario inputs,
the plans and the toolchain. Nothing else. The fit statistic lives in
`src/calibrate/`, and the holdout rows are never opened by either.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'analyse'))
from sample_population import subsample_plans, scale_transit_capacity  # noqa: E402
import registry  # noqa: E402
# The run emits its config through the SAME registry-driven path the builder
# uses. Importing the builder is deliberate: two code paths writing one config
# is how the shipped config and the run config came to disagree.
sys.path.insert(0, os.path.join(HERE, '..', 'build'))
import build_matsim_run_inputs as build_inputs  # noqa: E402
import city  # noqa: E402
import results_store  # noqa: E402
import run_failure  # noqa: E402
import summarise_run  # noqa: E402
from registry import outputs, param_config  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))


def _java_exe():
    """The pinned JDK's launcher, by platform (#128): `java.exe` on Windows,
    `java` elsewhere; the Windows name was typed in and no other platform
    could launch."""
    for cand in ('java.exe', 'java'):
        p = os.path.join(REPO, '.tools', 'jdk', 'bin', cand)
        if os.path.exists(p):
            return p
    return os.path.join(REPO, '.tools', 'jdk', 'bin',
                        'java.exe' if os.name == 'nt' else 'java')


JAVA = _java_exe()
JAR = os.path.join(REPO, '.tools', 'jars', 'pt2matsim-26.6-shaded.jar')
CLASSES = os.path.join(REPO, '.tools', 'classes')
# Our entry point, not MATSim's: it rebinds PermissibleModesCalculator so `ride`
# can be withheld from a person with nobody to drive them (DECISIONS.md 15,
# src/java/citysim/). The pinned jar is unchanged - this ADDS classes beside it.
MAIN = 'citysim.CitysimControler'
JAVA_SRC = os.path.join(REPO, 'src', 'java')
JAVA_SIGNALS_SRC = os.path.join(REPO, 'src', 'java_signals')


def refuse_unsafe_telemetry(cfg):
    """Refuse a run whose telemetry would have no memory barrier (#151).

    RunTelemetry's per-vehicle array and per-mode maps are written from the
    event-handler threads and read and cleared from the QSim thread, and it
    carries no volatile, no synchronized and no concurrent type. The sim-step
    barrier is the only thing publishing those writes. Turning it off does not
    crash the run - it silently tears the counters the progress digest then
    reports as a measurement, which is the worst shape a defect can take here.
    Checked before the JVM starts, and in the dry run, so a committed overlay
    that cannot legally run says so when it is resolved rather than hours in.
    """
    if (cfg.get('RUN.machine.telemetry_requires_simstep_barrier')
            and not cfg.get('RUN.machine.events_synchronize_on_simsteps')):
        raise SystemExit(
            'refused: RUN.machine.events_synchronize_on_simsteps is false '
            'while RUN.machine.telemetry_requires_simstep_barrier is true. '
            'RunTelemetry carries no volatile, no synchronized and no '
            'concurrent type; the sim-step barrier is the only thing that '
            'publishes its writes to the reading thread. Without it the live '
            'counters and the progress digest are silently torn, rather than '
            'wrong in a way anyone would see (#151). The barrier is also '
            'MEASURED faster on this model (DECISIONS.md 9.59). To run '
            'without it, make the shared state in RunTelemetry explicitly '
            'concurrent and declare the field false.')


def controler_sha256():
    """Hash the committed source of the entry point this run will execute.

    A run's identity (the parameter set in `_run.json`) cannot see the
    controler. That was harmless while the controler only rebound ride
    availability; issue #28 made it decide how `ride` gets its travel time,
    which moves every mode share. A result produced before that change and one
    produced after are different results with the same parameters, so the run
    record carries this and resume detection refuses to match across a change.

    Sources are hashed, not the compiled classes: javac output is not
    guaranteed byte-identical across JDK builds, and the source is what is
    committed and reviewable.
    """
    h = hashlib.sha256()
    # src/java_signals/ (the signals run stack, issue #73) is hashed alongside
    # src/java/: a change to either changes what a signal-enabled run executes,
    # and hashing both unconditionally is conservative - a resume refused on a
    # source change that could not have mattered costs a re-run, a resume
    # granted on one that did produces an untraceable result.
    for tree in (JAVA_SRC, JAVA_SIGNALS_SRC):
        for p in sorted(glob.glob(os.path.join(tree, '*', '*.java'))):
            h.update(os.path.basename(p).encode('utf-8'))
            with open(p, 'rb') as f:
                h.update(f.read())
    return h.hexdigest()


SETS = city.path('scenarios', 'matsim')
PLANS = city.path('demand', 'plans', 'matsim')
# The store owns the layout (DECISIONS.md 9.137): runs are CREATED under
# results/raw, records mirror into results/processed at every transition, and
# raw is a budgeted cache trimmed oldest-first. RESULTS stays pointed at the
# root only so legacy pre-migration paths keep resolving.
RESULTS = results_store.RESULTS
RAW = results_store.RAW


def fwd(p):
    return p.replace(os.sep, '/')


def setp(text, name, value, count=1):
    return re.sub(r'(<param name="%s" value=")[^"]*(")' % re.escape(name),
                  lambda m: m.group(1) + str(value) + m.group(2), text, count=count)


def set_mode_param(text, mode, name, value):
    """Set one scoring parameter inside a specific modeParams block."""
    pat = (r'(<parameterset type="modeParams">\s*<param name="mode" value="%s"[^>]*>'
           r'(?:(?!</parameterset>).)*?<param name="%s" value=")[^"]*(")'
           % (re.escape(mode), re.escape(name)))
    new, n = re.subn(pat, lambda m: m.group(1) + str(value) + m.group(2),
                     text, count=1, flags=re.S)
    if not n:
        raise SystemExit('no modeParams/%s/%s in the config' % (mode, name))
    return new


def resolve_warm_start(source):
    """The newest written plans checkpoint of a dead run, for `--warm-start`.

    A crashed 1000-iteration arm used to cost the whole arm: plans are written
    every `RUN.controler.write_plans_interval` iterations but the harness never
    fed them back (issue #75). This finds the newest `output/ITERS/it.N/
    N.plans.xml.gz` in the dead run directory and returns what the caller needs
    to start a NEW runner-named run from it. `output/output_plans.xml.gz` is
    deliberately not used: it is only written at a clean shutdown, so a run
    that has one did not crash and needs no warm start.

    THE CAVEAT IS STRUCTURAL, NOT FIXABLE HERE: a warm-started run is not
    bit-identical to an uninterrupted one - the RNG stream and the travel-time
    memory reset at the restart even though the plans carry over. Whether a
    warm-completed arm counts as a valid arm or a diagnostic is a project
    decision (DECISIONS.md 9.76); the provenance link written into `_meta.json`
    and `_run.json` (`warm_started_from`) is what makes that ruling possible
    after the fact.
    """
    source = os.path.abspath(source)
    meta_path = os.path.join(source, META)
    if not os.path.exists(meta_path):
        raise SystemExit('%s carries no %s - not a run directory' % (source, META))
    meta = json.load(open(meta_path, encoding='utf-8'))
    # A record no longer means the run reached its horizon - a run stopped at a
    # gate carries one too - so the refusal has to read the field and say which
    # of the two it is refusing. Both are refusals: warm restart is CRASH
    # RECOVERY. Resuming an arm past a gate the loop stopped it at would carry
    # the very deviation the gate fired on into the iterations after it, which
    # is the opposite of GOAL.md step 3 - the cause is fixed and the arm
    # relaunched, never continued.
    rec_path = os.path.join(source, '_run.json')
    if os.path.exists(rec_path):
        try:
            done = json.load(open(rec_path, encoding='utf-8')).get(
                'completion', RAN_TO_LAST)
        except (OSError, ValueError):
            done = RAN_TO_LAST
        if done == RAN_TO_LAST:
            raise SystemExit(
                '%s ran to its last iteration (its _run.json says %s). Warm '
                'restart is crash recovery; re-running it is --force.'
                % (source, RAN_TO_LAST))
        raise SystemExit(
            '%s was stopped deliberately, not crashed (its _run.json says %s) '
            'and is already closed out. Warm restart is crash recovery: fix '
            'what the stop found and launch a fresh arm - resuming past a gate '
            'carries the deviation it fired on into every iteration after it.'
            % (source, done))
    candidates = []
    for d in glob.glob(os.path.join(source, 'output', 'ITERS', 'it.*')):
        try:
            n = int(os.path.basename(d).split('.', 1)[1])
        except (IndexError, ValueError):
            continue
        p = os.path.join(d, '%d.plans.xml.gz' % n)
        if os.path.exists(p):
            candidates.append((n, p))
    if not candidates:
        raise SystemExit(
            '%s holds no written plans checkpoint (output/ITERS/it.N/'
            'N.plans.xml.gz). It died before the first plans write, so a cold '
            'start loses nothing.' % source)
    n, plans = max(candidates)
    return dict(run=os.path.basename(source), iteration=n, plans=plans,
                meta=meta)


def check_warm_compatibility(warm, scenario, day, fraction, seed, threads,
                             overrides):
    """Refuse a warm start whose parent run is a different experiment.

    The checkpoint plans are already sampled at the parent's fraction and
    already carry the parent's demand, so every identity parameter must match:
    scenario, day, fraction, seed, and threads (the mobsim partitions by thread
    count - DECISIONS.md 9.56/9.59 make threads run identity, not a knob). Raw
    `--set` overrides must match too, or the resumed run continues a different
    model than the one that wrote the plans.
    """
    m = warm['meta']
    for key, ours in (('scenario', scenario), ('day', day),
                      ('fraction', fraction), ('seed', seed),
                      ('threads', threads)):
        theirs = m.get(key)
        if theirs is not None and theirs != ours:
            raise SystemExit(
                'warm start refused: %s ran %s=%r, this invocation resolves '
                '%r. A checkpoint is only a checkpoint of its own '
                'parameters.' % (warm['run'], key, theirs, ours))
    if (m.get('overrides') or {}) != (overrides or {}):
        raise SystemExit(
            'warm start refused: %s ran with raw overrides %r, this '
            'invocation carries %r. The checkpoint plans embody the '
            "parent's model; resume it with the same overrides."
            % (warm['run'], m.get('overrides') or {}, overrides or {}))


def build_config(src_dir, run_dir, scenario, day, fraction, seed, overrides, cfg,
                 warm=None):
    """EMIT this run's config from this run's resolution, not patch the shipped one.

    It used to read the committed `config.xml` and rewrite six parameters into
    it. That meant a run overlay could only ever move those six: any other field
    it set was accepted by the resolver, validated against its sweep, written
    into `_config.json` as the run's provenance - and could not reach the model,
    because the shipped config still carried the builder's value. The snapshot
    said one thing and the run did another, which is this repository's signature
    defect wearing the provenance record as a disguise.

    The config is now built from the SAME registry-driven emitter the builder
    uses, against the scenario, day, run overlay, environment and --set layers
    this run actually resolved. Every declared field reaches the model or the
    closure check fails.
    """
    base = os.path.join(SETS, scenario)

    plans_src = os.path.join(PLANS, 'population_%s.xml.gz' % day)
    plans_dst = os.path.join(run_dir, 'plans.xml.gz')
    veh_src = os.path.join(src_dir, 'transitVehicles.xml.gz')
    veh_dst = os.path.join(run_dir, 'transitVehicles.xml.gz')
    if warm is not None:
        # The checkpoint plans are ALREADY SAMPLED at the parent's fraction
        # (check_warm_compatibility enforced the match), so the subsampler must
        # not run again - a second pass would sample the sample. The file is
        # copied into the run directory so the new run is self-contained even
        # after the dead parent is cleaned up or pruned.
        shutil.copyfile(warm['plans'], plans_dst)
        n_in = n_out = n_hhless = None
        if fraction >= 1.0 or not cfg.get('RUN.sample.transit_capacity_scaling'):
            shutil.copyfile(veh_src, veh_dst)
            scaled = []
        else:
            scaled = scale_transit_capacity(
                veh_src, veh_dst, fraction,
                cfg.get('RUN.sample.transit_capacity_floor'))
    elif fraction >= 1.0:
        n_in = n_out = n_hhless = None
        plans_dst, veh_dst = plans_src, veh_src
        scaled = []
    else:
        n_in, n_out, n_hhless = subsample_plans(
            plans_src, plans_dst, fraction, seed,
            cfg.get('RUN.sample.unit'))
        # The sampling UNIT is declared (DECISIONS.md 9.45). A person-wise
        # sample shreds households, and every household-coupled mechanism
        # then depends on the fraction rather than on the demand - which is
        # the one thing a sample fraction must not decide.
        # The switch DECIDES this now. It was declared as "not optional in
        # practice - at a 10% sample an unscaled bus carries 700 real people, so
        # capacity never binds and crowding silently disappears" and then read
        # by nothing, which is the failure it warns about.
        if cfg.get('RUN.sample.transit_capacity_scaling'):
            scaled = scale_transit_capacity(
                veh_src, veh_dst, fraction,
                cfg.get('RUN.sample.transit_capacity_floor'))
        else:
            shutil.copyfile(veh_src, veh_dst)
            scaled = []

    refuse_unsafe_telemetry(cfg)

    # The parking price table sits beside the scenario network, one per scenario.
    # Checked rather than assumed: a config that lost its price file would run
    # with free parking and look exactly like a correct run (issue #33).
    price_src = os.path.join(base, 'parking_prices.tsv')
    if not os.path.exists(price_src):
        raise SystemExit(
            'no parking price table at %s. Regenerate the run inputs with '
            'build_matsim_run_inputs.py.' % price_src)

    # Explicit corridor signals (#73): under the explicit representation the
    # run consumes the generated signal data model for ITS scenario. The
    # files are checked here, in 0.1 s, rather than in the JVM.
    signal_paths = {}
    if cfg.get('A.signals.representation') == 'explicit_signals':
        sig_dir = city.path('networks', 'matsim', 'signals', scenario)
        for key, name in (('signal_systems', 'signal_systems.xml'),
                          ('signal_groups', 'signal_groups.xml'),
                          ('signal_control', 'signal_control.xml')):
            p = os.path.join(sig_dir, name)
            if not os.path.exists(p):
                raise SystemExit(
                    'A.signals.representation is explicit_signals but %s is '
                    'missing. Run cities/<city>/build/build_matsim_signals.py '
                    'first.' % p)
            signal_paths[key] = fwd(p)
        # The controller identifier is baked into the generated control file,
        # so a declared regime that disagrees with the committed artefact
        # would reach NOTHING - the run would execute the other controller and
        # complete happily. Checked here in 0.1 s (DECISIONS.md 9.88).
        want = ('CitysimScats'
                if cfg.get('A.signals.control_regime') == 'scats_adaptive'
                else None)
        ctl = os.path.join(sig_dir, 'signal_control.xml')
        with open(ctl, encoding='utf-8') as fh:
            control_text = fh.read()
        has_scats = 'CitysimScats' in control_text
        if want and not has_scats:
            raise SystemExit(
                'A.signals.control_regime is scats_adaptive but %s names no '
                'CitysimScats controller. The identifier is generated into '
                'the control file, so the regime must be regenerated with it: '
                'python cities/<city>/build/build_matsim_signals.py' % ctl)
        if not want and has_scats:
            raise SystemExit(
                'A.signals.control_regime is %r but %s names the CitysimScats '
                'controller. Regenerate the signal data for the declared '
                'regime: python cities/<city>/build/build_matsim_signals.py'
                % (cfg.get('A.signals.control_regime'), ctl))
    # Level crossings (#68): the closures enter this run's re-emitted config
    # only under the declared representation gate - same rule as the shipped
    # assembly, checked here in 0.1 s rather than in the JVM.
    if cfg.get('A.crossings.representation') == 'change_events':
        p = city.path('networks', 'matsim', 'crossings',
                      'crossing_change_events.xml')
        if not os.path.exists(p):
            raise SystemExit(
                'A.crossings.representation is change_events but %s is '
                'missing. Run cities/<city>/build/build_level_crossings.py '
                'first.' % p)
        signal_paths['change_events'] = fwd(p)

    # Both capacity factors are identities on the sample fraction, and NEITHER
    # is a choice. Checked here, in 0.1 s, rather than in the JVM a second
    # later: MATSim's GlobalConfigGroup.checkConsistency throws when the two
    # differ by more than global.relativeTolerance, which defaults to 0.0.
    storage = fraction ** cfg.get('RUN.sample.storage_capacity_exponent')
    if abs(storage - fraction) > 1e-12:
        raise SystemExit(
            'storageCapacityFactor (%g) must equal flowCapacityFactor (%g). MATSim '
            'enforces this and states that raising storage above flow "is no longer '
            'needed since the qsim became a lot more deterministic". '
            'RUN.sample.storage_capacity_exponent is 1.0 by derivation, not by '
            'assumption - see DECISIONS.md 15.' % (storage, fraction))

    build_inputs.check_scoring_order(cfg)
    scoring = build_inputs.scoring_from_c1(
        cfg, json.load(open(build_inputs.PARAMS, encoding='utf-8')),
        purpose_share())
    # The per-main-mode vehicle types are REGENERATED from this run's own
    # resolution, not copied from the shipped set: B.freight.pce is a swept
    # field, and a run overlay moving it must move the truck the mobsim
    # actually loads (DECISIONS.md 9.49).
    mode_veh = build_inputs.write_mode_vehicles(
        os.path.join(run_dir, 'vehicles.xml'), cfg)
    paths = dict(
        output=fwd(os.path.join(run_dir, 'output')),
        network=fwd(os.path.join(base, 'network.xml.gz')),
        plans=fwd(plans_dst),
        schedule=fwd(os.path.join(src_dir, 'transitSchedule.xml.gz')),
        vehicles=fwd(veh_dst),
        mode_vehicles=fwd(mode_veh),
        parking_prices=fwd(price_src),
        fraction=fraction,
        **signal_paths)
    config_path = build_inputs.write_config(
        os.path.join(run_dir, 'config.xml'), cfg, scoring, day, paths)
    # an override the run would record and not execute is refused here, with
    # the emitted config and vehicle types in hand to test it against
    refuse_unrealised_overrides(
        cfg, scoring, day, paths,
        dict(config=open(config_path, encoding='utf-8').read(),
             vehicles=open(mode_veh, encoding='utf-8').read()))

    # Raw MATSim overrides (`--set ride.constant=-3.4`) are applied after the
    # emission, deliberately: they are an escape hatch BELOW the registry, for
    # probing a parameter directly, and they are recorded in the run record so a
    # result carries them. A registry field must never be varied this way -
    # --config-set is checked against the declared sweep and this is not.
    if overrides:
        text = open(config_path, encoding='utf-8').read()
        for key, value in sorted(overrides.items()):
            if '.' in key:
                mode, name = key.split('.', 1)
                text = set_mode_param(text, mode, name, value)
            else:
                text = setp(text, key, value)
        open(config_path, 'w', encoding='utf-8', newline='\n').write(text)
    return config_path, dict(persons_in=n_in, persons_kept=n_out,
                             unit=cfg.get('RUN.sample.unit'),
                             persons_without_household=n_hhless,
                             transit_capacity_scaled=sorted(set(scaled)))


_PURPOSE_SHARE = {}


def purpose_share():
    """The HTS purpose weights the C1 translation is averaged over.

    Read from the run-inputs report the builder wrote, not recomputed: the
    weights come from a pandas read of the HTS tables, and a run should not
    depend on that at start-up. The DERIVED SCORING is still recomputed here
    against this run's own resolution, so a run overlay moving the transfer
    penalty moves utilityOfLineSwitch with it - which is the whole point of
    emitting rather than patching.
    """
    if not _PURPOSE_SHARE:
        report = os.path.join(SETS, '_run_inputs_report.json')
        if not os.path.exists(report):
            raise SystemExit(
                'no %s. The run inputs must be assembled before a run: '
                'python src/build/build_matsim_run_inputs.py' % report)
        doc = json.load(open(report, encoding='utf-8'))
        if 'purpose_share' not in doc:
            raise SystemExit(
                '%s predates the registry-driven config emitter and carries no '
                'purpose_share. Regenerate the run inputs.' % report)
        _PURPOSE_SHARE.update(doc['purpose_share'])
    return _PURPOSE_SHARE


ITER_RE = re.compile(r'### ITERATION (\d+) (BEGINS|ENDS)')
TS_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}),(\d{3})')


def iteration_times(log):
    """Wall seconds per iteration, from the controller's own markers.

    Prefers the digest's running record (`_progress.json`'s
    `iteration_seconds`, written from the same two markers as the run
    proceeded) and falls back to walking the log when a run carries none - an
    arm that predates the field, or one whose digest never started. The
    fallback is a FULL sequential read: the F23 arm's matsim.log was 54.9 GB
    (9.142), and close-out wanted a median out of it.
    """
    import datetime as dt
    recorded = _recorded_iteration_times(log)
    if recorded:
        return recorded
    begins, out = {}, {}
    with open(log, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = ITER_RE.search(line)
            t = TS_RE.match(line)
            if not m or not t:
                continue
            ts = (dt.datetime.strptime(t.group(1), '%Y-%m-%dT%H:%M:%S').timestamp()
                  + int(t.group(2)) / 1000.0)
            if m.group(2) == 'BEGINS':
                begins[int(m.group(1))] = ts
            elif int(m.group(1)) in begins:
                out[int(m.group(1))] = round(ts - begins[int(m.group(1))], 2)
    return out


def announce_cost(iterations, fraction, cfg):
    """Say what this run will cost BEFORE it starts, from the runs on disk.

    The rule is written in three documents - price the arm on the newest arm's
    own median - and it was still broken by hand: the F30 arm was quoted at
    260 s an iteration from the arm before it, ran at 376, and was stopped on
    cost at iteration 23 with nothing measured (9.153). A price a human carries
    between documents is a price that rots, so the launcher reads it.

    It never refuses a launch. The approval is the user's and the rules that
    gate a launch are elsewhere; this only makes sure the number in front of
    them is the newest measured one.
    """
    try:
        sys.path.insert(0, os.path.join(REPO, 'src'))
        from analyse import arm_cost
        quote = arm_cost.price(int(iterations), fraction,
                               arm_cost.observed_arms(),
                               cfg.get('RUN.gate.interval_iterations'))
    except Exception as e:                                   # noqa: BLE001
        print('cost: not priced (%s)' % e, flush=True)
        return
    if quote.get('error'):
        print('cost: %s' % quote['error'], flush=True)
        return
    on = quote['priced_on']
    line = ('cost: ~%s for %d iterations plus %s of setup, priced on %s at '
            '%.1f s an iteration (%s); the last arms at this fraction span '
            '%s to %s'
            % (quote['quote'], quote['iterations'],
               arm_cost._fmt_hours(quote['setup_s']), on['name'],
               on['median_iteration_s'], on['completion'] or 'status unknown',
               quote['band'][0], quote['band'][1]))
    if quote.get('first_gate_s'):
        line += '; first gate at iteration %d after ~%s' % (
            quote['gate_every'],
            arm_cost._fmt_hours(quote['first_gate_s']))
    print(line, flush=True)
    # A stated ceiling is only a boundary if something holds it. Until #169 the
    # sentence below was the whole mechanism, and an arm that disabled the gate
    # watcher had no automatic stop at all - so say which of the two this run is.
    try:
        ceiling_h = float(cfg.get('RUN.gate.wall_ceiling_h'))
    except Exception:                                        # noqa: BLE001
        ceiling_h = 0.0
    if ceiling_h > 0:
        print('      A STATED COST IS A BOUNDARY, AND THIS ONE IS ENFORCED: '
              'the runner stops itself at RUN.gate.wall_ceiling_h = %g h '
              '(#169).' % ceiling_h, flush=True)
    else:
        print('      A STATED COST IS A BOUNDARY, NOT AN ESTIMATE. Stop the '
              'arm at the cost that was approved. THIS RUN DECLARES NO '
              'CEILING (RUN.gate.wall_ceiling_h = 0), so nothing will stop it '
              'on cost - set it on the overlay beside the approval it encodes '
              '(#169).', flush=True)


def parse_heap_gib(xmx):
    """The GiB a JVM `-Xmx` string denotes ('40g', '14000m', '2t'), or None."""
    m = re.match(r'^\s*(\d+(?:\.\d+)?)\s*([kmgt]?)\s*$', str(xmx or ''), re.I)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2).lower()
    return n * {'k': 1.0 / 1048576, 'm': 1.0 / 1024, 'g': 1.0, 't': 1024.0,
                '': 1.0 / (1024 ** 3)}[unit]


def heap_floor_gib(cfg, fraction):
    """The smallest heap the registry's own rule admits at this fraction.

    `RUN.machine.xmx` has carried the rule "must exceed 9.6 GiB + 87 GiB x
    fraction or the run dies" in its description since 9.5, and nothing read
    it: F33's arm 0 launched on the 14 g default at 25 % (31.4 GiB by the
    rule), ran 20.9 h and threw OutOfMemoryError at iteration 98. The two
    terms are declared fields now, so the rule is a number the launcher can
    compare rather than a sentence a person has to remember (eighth report,
    11 September 2026; #66, #172).
    """
    return (float(cfg.get('RUN.machine.heap_floor_gib'))
            + float(cfg.get('RUN.machine.heap_per_fraction_gib')) * float(fraction))


def refuse_small_heap(cfg, xmx, fraction):
    """Refuse a launch whose heap the registry's own rule says will die.

    A pricing probe prices TIME and cannot price HEAP: plan memory fills over
    the first ~100 iterations and a four-iteration probe sees none of it, so
    the only protection that costs nothing is to read the rule before the JVM
    starts. Like the other refusals this prints the fields and the overlay
    line that would satisfy it; it never adjusts the heap on its own, because
    the heap is part of the approved cost.
    """
    have = parse_heap_gib(xmx)
    if have is None:
        raise SystemExit('REFUSED: RUN.machine.xmx = %r is not a JVM heap size '
                         '(expected e.g. 40g).' % (xmx,))
    need = heap_floor_gib(cfg, fraction)
    if have + 1e-9 >= need:
        return
    raise SystemExit(
        'REFUSED: RUN.machine.xmx = %s is below the heap the registry\'s own rule '
        'requires at a %.2f sample: %.1f GiB (RUN.machine.heap_floor_gib %s + '
        'RUN.machine.heap_per_fraction_gib %s x fraction). F33\'s arm 0 launched '
        'on 14g at 25%% and died of OutOfMemoryError at iteration 98 after 20.9 h. '
        'Set RUN.machine.xmx on the overlay, beside the approval it encodes.'
        % (xmx, float(fraction), need, cfg.get('RUN.machine.heap_floor_gib'),
           cfg.get('RUN.machine.heap_per_fraction_gib')))


class _AtBase(object):
    """A resolution with ONE field answered from the registry, not the overlay."""

    def __init__(self, inner, key):
        self._inner, self._key = inner, key

    def get(self, k, caller=None):
        if k == self._key:
            return self._inner.field(k).get('value')
        return self._inner.get(k, caller=caller)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def refuse_unrealised_overrides(cfg, scoring, day, paths, emitted):
    """Refuse a run overlay or --config-set that moves a field this run cannot read.

    No registry field carries a stage, so the resolver admits any field into a
    run overlay on membership alone: `A.parking.search_min_max` is baked into
    the run inputs at assembly, and an overlay setting it is validated,
    recorded in `_config.json` as moved, and executes the base value (eighth
    project report, 11 September 2026; area 4). The test here is the exact
    one: with the field put back to its registry value, does anything this
    run READS change - the emitted config, or the per-mode vehicle types the
    runner regenerates? If neither moves, the override would be recorded and
    not executed, which is the defect this refusal exists for, and the launch
    is refused with the key and where its change would have to be realised.

    RUN.* and CAL.* keys are the run's own and the loop's own; the former are
    read by the runner itself rather than through the config (threads, heap,
    the watchers), so they are never tested here. The calibrator's stage table
    (`calibrate.rebuild_stage`) is the coarser reading of the same question
    and classes every field `build_matsim_run_inputs.py` consumes as needing
    the run inputs regenerated - which is wrong for the fields `config_runtime`
    derives at launch (the taxi fare blend, the score-MSA fraction, the
    capacity factors); this test sees those as realised because they are.
    """
    import tempfile                                           # noqa: PLC0415
    snap = cfg.snapshot()
    keys = [k for k, origin in snap['resolved_from'].items()
            if (origin.startswith('run:') or origin in ('set', 'env'))
            and not (k.startswith('RUN.') or k.startswith('CAL.'))]
    if not keys:
        return
    bad = []
    for key in keys:
        at_base = _AtBase(cfg, key)
        try:
            base_scoring = build_inputs.scoring_from_c1(
                at_base, json.load(open(build_inputs.PARAMS, encoding='utf-8')),
                purpose_share())
            runtime = build_inputs.config_runtime(at_base, base_scoring, day, paths)
            text = param_config.emit('matsim', at_base, runtime)
            with tempfile.TemporaryDirectory() as td:
                veh = build_inputs.write_mode_vehicles(
                    os.path.join(td, 'vehicles.xml'), at_base)
                veh_text = open(veh, encoding='utf-8').read()
        except Exception as e:                                # noqa: BLE001
            # a derivation that cannot run at the base value is a change the
            # run does read - it is the override making the derivation valid
            continue
        if text != emitted['config'] or veh_text != emitted['vehicles']:
            continue
        consumers = ', '.join(cfg.field(key).get('consumers') or []) or 'no declared consumer'
        bad.append('  %s (from %s): consumed by %s' % (key, snap['resolved_from'][key], consumers))
    if not bad:
        return
    raise SystemExit(
        'REFUSED: this run would RECORD a change it cannot EXECUTE. Put back to '
        'the registry value, none of these keys changes the emitted config or the '
        'vehicle types this run reads - their change is realised only by a '
        'rebuild of the stage their consumer belongs to:\n%s\nRebuild that '
        'stage, or drop the key from the overlay.' % '\n'.join(bad))


def refuse_if_no_automatic_stop(cfg):
    """A run must be able to stop itself on SOMETHING. This refuses one that cannot.

    Two independent stops exist and they have different owners: the gate
    watcher stops on the MODEL being wrong (`RUN.gate.interval_iterations`
    iterations, any mode past the stop bar) and the ceiling watcher stops on
    the RUN being expensive (`RUN.gate.wall_ceiling_h`). Either is a boundary.
    Neither is a boundary that holds when both are off, and #169 named that
    state precisely: an arm that disables the gate watcher "has no automatic
    stop at all - not on deviation, and not on cost".

    That is not hypothetical. `depth_convergence_25pct` set
    `RUN.gate.interval_iterations = 0` for a defensible, recorded reason - an
    arm measuring where a reading settles cannot be stopped at the point under
    test (9.159) - and declared no ceiling, so its approved 32 h was enforced
    by a person watching a clock. It ran 21.5 h unattended. The precedent it
    was launched against is on the record: at 9.153 an arm ran 45% over its
    price and was stopped by whoever happened to be looking.

    The launcher otherwise never refuses a launch, and this does not change
    that for any run that keeps one stop. Turning the gate watcher off stays
    entirely legitimate; it now costs one more line on the overlay, beside the
    approval that line encodes. `RUN.gate.interval_iterations = 0` keeps
    meaning "do not judge my modes" and never "do not enforce my budget".
    """
    try:
        interval = int(cfg.get('RUN.gate.interval_iterations'))
    except (TypeError, ValueError):
        interval = 0
    try:
        ceiling_h = float(cfg.get('RUN.gate.wall_ceiling_h'))
    except (TypeError, ValueError):
        ceiling_h = 0.0
    # 9.164 (#131): AN INTERVAL IS NOT A GATE. The watcher reads what the
    # monitor maintains and refuses to arm without it, so an interval declared
    # beside `RUN.monitor.enabled = false` is a stop that does not exist -
    # measured on 20260910T205517_20it_1pct, which declared an interval of 2,
    # reached iteration 3 and wrote no verdict, no gate line and no warning.
    # This refusal counted such a run as protected because it read the
    # interval alone.
    monitored = bool(cfg.get('RUN.monitor.enabled'))
    if (interval > 0 and monitored) or ceiling_h > 0:
        return
    raise SystemExit(
        'REFUSED: this run has no automatic stop of any kind.\n'
        '  RUN.gate.interval_iterations = %d, RUN.monitor.enabled = %s  (%s, '
        'so nothing stops it on the model being wrong)\n'
        % (interval, str(monitored).lower(),
           'the gate watcher is off' if interval <= 0
           else 'the gate watcher cannot arm without the monitor it reads, '
                '#131') +
        '  RUN.gate.wall_ceiling_h      = 0  (no ceiling, so nothing stops it '
        'on cost)\n'
        'An arm in this state runs until it finishes or a person notices, and '
        'a stated-cost approval it cannot enforce is a sentence rather than a '
        'boundary (#169).\n'
        'Set RUN.gate.wall_ceiling_h on the overlay, beside the approval it '
        'encodes - turning the gate watcher off is legitimate and stays so.')


def _recorded_iteration_times(log):
    """`_progress.json`'s `iteration_seconds` for this run, or {}."""
    path = os.path.join(os.path.dirname(log), '_progress.json')
    try:
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return {}
    raw = doc.get('iteration_seconds')
    if not isinstance(raw, dict) or not raw:
        return {}
    out = {}
    for k, v in raw.items():
        try:
            out[int(k)] = float(v)
        except (TypeError, ValueError):
            return {}
    return out


def warm_start_overrides(warm, overrides, scenario, day, run_config):
    """The overrides a warm start needs so the resumed run keeps its cutoff.

    `firstIteration` alone is not enough. The pinned jar computes the
    innovation cutoff as `first + f x (last - first)` (StrategyManager.class,
    read with javap), so a resume at N = 100 with the declared f = 0.8 over a
    300-iteration horizon innovates to 100 + 0.8 x 200 = 260, not the 240 the
    parent arm was searching to - the comment that used to sit here claimed
    the two lined up, and they did not (eighth report, 11 September 2026;
    #192). The fraction is re-derived so the cutoff ITERATION is preserved:
    f' = (cutoff - N) / (last - N). It goes through the registry's own set
    layer like every override, so a derived value outside the field's sweep
    is refused there with the field's own message - a resume that cannot keep
    its cutoff inside the declared sweep is a run the operator must overlay
    deliberately, not one the harness may quietly reshape.
    """
    base = registry.load(scenario=scenario, day=day, run=run_config,
                         set=dict(overrides))
    first = int(base.get('RUN.controler.first_iteration'))
    last = int(base.get('RUN.controler.last_iteration'))
    f = float(base.get('RUN.replanning.fraction_to_disable_innovation'))
    n = int(warm['iteration'])
    cutoff = first + f * (last - first)
    if last <= n:
        raise SystemExit('warm start: the checkpoint iteration %d is not below '
                         'RUN.controler.last_iteration = %d' % (n, last))
    derived = (cutoff - n) / float(last - n)
    out = dict(overrides)
    out['RUN.controler.first_iteration'] = n
    out['RUN.replanning.fraction_to_disable_innovation'] = round(derived, 6)
    print('warm start: innovation cutoff kept at iteration %.0f - '
          'fraction_to_disable_innovation %g -> %g for firstIteration %d'
          % (cutoff, f, round(derived, 6), n), flush=True)
    return out


def resolve(scenario, day, run_config=None, set_overrides=None):
    """Resolve the input registry for this run, and fail loudly if it will not.

    `RUN.controler.last_iteration` is declared UNOBTAINED, so this raises unless
    the caller supplied one. That is deliberate: DECISIONS.md 9.7 shows 100 and
    250 are both measurably too low and no justified value has been measured, so
    the registry refuses to invent one rather than shipping another guess.
    """
    try:
        return registry.load(scenario=scenario, day=day, run=run_config,
                             set=set_overrides)
    except registry.RegistryError as e:
        raise SystemExit(str(e))


def start_live_view(run_dir, cfg):
    """Serve this run's live view and return its url, or None.

    One server per run, on its own port. `RUN.monitor.port` is the FIRST port
    tried, not the only one, so concurrent runs each get their own view instead
    of competing for a single fixed port.

    It can never stop a run. The server thread is a daemon and every failure
    here is reported and swallowed: a run that dies because its instrumentation
    could not bind a socket is worse than a run with no instrumentation. The
    import is deferred for the same reason - the view is optional, the run is
    not.
    """
    if not cfg.get('RUN.monitor.enabled'):
        return None
    try:
        import run_view                                   # noqa: PLC0415
        return run_view.serve(run_dir, port=cfg.get('RUN.monitor.port'),
                              poll_s=cfg.get('RUN.monitor.poll_s'),
                              background=True)
    except Exception as exc:                              # noqa: BLE001
        print('live view unavailable: %s' % exc, flush=True)
        return None


def start_progress_digest(run_dir, cfg):
    """Start the `_progress.json` writer beside the live view (issue #76).

    Gated on the same observer switch, running on the same terms: a daemon
    thread that reads the run directory, writes one file atomically, and can
    never stop a run. The import is deferred because the digest is optional
    and the run is not.
    """
    if not cfg.get('RUN.monitor.enabled'):
        return None
    try:
        import progress_digest                            # noqa: PLC0415
        return progress_digest.serve(
            run_dir, cfg.get('RUN.monitor.progress_interval_s'),
            band=cfg.get('RUN.monitor.pace_band_s'), background=True)
    except Exception as exc:                              # noqa: BLE001
        print('progress digest unavailable: %s' % exc, flush=True)
        return None



def inputs_sha256(day):
    """A fingerprint of the population this run samples from (9.127).

    The run's identity has to include WHAT it ran on. Scenario, day, fraction,
    seed, overrides, the controler hash and the resolved values did not see a
    rebuilt population: the second F18 chain's smoke probe resumed the 16:10
    probe on the old plans and reported "passed". The sha256 of the day's
    population file joins the key; a record written before this was tracked
    carries none and does not match, as with the values hash.
    """
    path = os.path.join(PLANS, 'population_%s.xml.gz' % day)
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def values_sha256(cfg):
    """A fingerprint of every resolved registry value this run will use.

    Run identity has to include what the model was CONFIGURED with, not only
    its parameters and its source. A run-config overlay sets registry fields,
    so without this two overlays that differ in exactly one declared value -
    which is what a paired diagnostic IS - are indistinguishable to resume, and
    the second silently inherits the first's results (9.104). The same
    conservatism applies as to the controler hash: a resume refused on a value
    change that could not have mattered costs a re-run, a resume granted on one
    that did produces a comparison whose two sides are not the same thing.
    """
    values = cfg.snapshot()['values']
    blob = json.dumps(values, sort_keys=True, ensure_ascii=False,
                      default=str).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()


# The three boundaries at which a run can END rather than die. `completion` in
# the record names one of them, and only the first says the run executed the
# horizon it declared - which is NOT a claim of convergence, held separately by
# DECISIONS.md 9.7. A run that CRASHED reaches none of them and gets no record.
RAN_TO_LAST = 'ran_to_last_iteration'
STOPPED_AT_GATE = 'stopped_at_gate'
# The COST boundary, as against the gate's modelling one (#169).
STOPPED_AT_CEILING = 'stopped_at_ceiling'
# The LIVENESS boundary (eighth report, 11 September 2026): a JVM that writes
# nothing for RUN.gate.stall_kill_s is stopped, because the alternative was
# measured - 13.1 h of one iteration on an awake machine, seen by the digest
# at 05:13 and killed by nobody.
STOPPED_AT_STALL = 'stopped_at_stall'
STOPPED_BY_OPERATOR = 'stopped_by_operator'


def find_completed(scenario, day, fraction, iterations, seed, overrides,
                   controler=None, warm_key=None, values=None, inputs=None):
    """The completed run with these parameters, if one exists.

    Identity lives in the run record, not in the directory name: the name is a
    launch-time label, so resume has to compare what was actually run. A run
    that crashed leaves no `_run.json` and is invisible here, exactly as before.

    ONLY A RUN THAT REACHED ITS HORIZON CAN BE RESUMED. Since a run stopped at a
    gate also carries a record, presence alone is no longer the test: without
    the `completion` check below, relaunching the very overlay whose arm the
    gate stopped would print `resume: already complete` and run nothing - the
    session would read a stopped arm as a finished one. Records written before
    the field existed were only ever written on rc=0, so a missing value reads
    as `ran_to_last_iteration`.

    A record whose controler hash matches `controler` is preferred over one
    whose does not: the same parameter set legitimately exists across model
    families (the 18 Aug pilot arm and the 21 Aug base arm share every
    parameter), and only the hash tells them apart. Newest first, so a forced
    re-run supersedes what it re-ran. The returned record's `name` is set to
    the directory that actually holds it - directories are renameable labels,
    and a record must never point a caller at a name its directory no longer
    carries.
    """
    fallback = None
    for record in sorted(glob.glob(os.path.join(RAW, '*', '_run.json'))
                         + glob.glob(os.path.join(results_store.PROCESSED,
                                                  '*', '_run.json'))
                         + glob.glob(os.path.join(RESULTS, '*', '_run.json')),
                         reverse=True):
        try:
            doc = json.load(open(record, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if (doc.get('completion', RAN_TO_LAST) == RAN_TO_LAST
                and doc.get('scenario') == scenario and doc.get('day') == day
                and doc.get('fraction') == fraction
                and doc.get('iterations') == iterations
                and doc.get('seed') == seed
                and (doc.get('overrides') or {}) == (overrides or {})
                # A warm-started run and a cold one with the same parameters
                # are DIFFERENT results (the RNG stream and travel-time memory
                # reset at the checkpoint), so neither may resume the other.
                and (doc.get('warm_started_from') or None) == (warm_key or None)
                # The resolved registry values are part of run identity: a
                # run-config overlay sets declared fields, so two overlays
                # differing in ONE value are the same parameter set here and
                # the second would inherit the first's result (9.104). A
                # record written before this was tracked carries no hash and
                # cannot prove it used the same values, so it does not match -
                # a re-run costs time, a false resume costs a finding.
                and (values is None
                     or doc.get('values_sha256') == values)
                # 9.127: and the population it sampled from - a rebuilt
                # demand under the same parameters is a different run
                and (inputs is None
                     or doc.get('inputs_sha256') == inputs)
                and doc.get('rc') == 0):
            doc['name'] = os.path.basename(os.path.dirname(record))
            if controler is None or doc.get('controler_sha256') == controler:
                return doc
            if fallback is None:
                fallback = doc
    return fallback


META = '_meta.json'


def _now():
    return time.strftime('%Y-%m-%dT%H:%M:%S')


def write_meta(run_dir, doc):
    outputs.write_checked(os.path.join(run_dir, META), doc, 'meta')
    # Every record transition lands in processed the moment it happens, so a
    # run's findings exist even if its bulk never survives to be processed
    # (a crash mid-run, a trim later). Mirroring must never kill a run.
    try:
        results_store.mirror(run_dir)
    except Exception as e:                                   # noqa: BLE001
        print('record mirror failed (%s): %s' % (run_dir, e), flush=True)


def update_meta(run_dir, **changes):
    """Best-effort status transition: observability must never kill a run."""
    path = os.path.join(run_dir, META)
    try:
        doc = json.load(open(path, encoding='utf-8'))
        doc.update(changes)
        write_meta(run_dir, doc)
    except Exception as e:                                   # noqa: BLE001
        print('run metadata not updated (%s): %s' % (path, e), flush=True)


def _pid_alive(pid):
    """Is this pid a live process? Never signals anything.

    On Windows `os.kill(pid, 0)` TERMINATES the process (os.kill there only
    wraps TerminateProcess and the CTRL events), so liveness is asked of the
    kernel handle instead.
    """
    if os.name == 'nt':
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x00100000, 0, int(pid))    # SYNCHRONIZE
        if not handle:
            return False
        rc = k32.WaitForSingleObject(handle, 0)
        k32.CloseHandle(handle)
        return rc == 0x102                                   # WAIT_TIMEOUT: alive
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def mark_dead(run_dir, status, rc=None, wall_s=None, cause=None):
    """Record a run's death in its metadata and rename it aborted_<name>.

    The prefix is a label so a person scanning `results/` can disregard the
    directory without opening it; the PRECISE status (failed vs aborted) lives
    in `_meta.json`. If the rename loses to a Windows directory lock (a
    `tail -f` monitor is enough to hold one), the metadata still carries the
    truth and the rename is reported, not raised.

    IT ALSO RECORDS WHY. A card that says `failed, rc=1` and nothing else leaves
    the reason with whoever happened to be watching; three 25 August probe
    failures reached the next session as directories that could not explain
    themselves. The cause is READ FROM THE RUN'S OWN LOG (`run_failure.py`), so
    it is evidence rather than recollection. Where the caller knows something
    the log cannot - an interrupt, a dead harness - that is the headline and the
    log's last word is kept beside it.
    """
    found = run_failure.diagnose(run_dir, status, rc)
    from_log = found.pop('cause')
    changes = dict(status=status, ended=_now(), rc=rc, wall_s=wall_s,
                   cause=cause or from_log)
    if cause and from_log:
        found['log_says'] = from_log
    detail = {k: v for k, v in found.items() if v not in (None, [], '')}
    if detail:
        changes['cause_detail'] = detail
    update_meta(run_dir, **changes)
    parent, name = os.path.split(os.path.abspath(run_dir))
    if name.startswith('aborted_'):
        return run_dir
    target = os.path.join(parent, 'aborted_' + name)
    n = 2
    while os.path.exists(target):
        target = os.path.join(parent, 'aborted_%s-%d' % (name, n))
        n += 1
    try:
        os.rename(run_dir, target)
    except OSError as e:
        print('could not rename %s -> %s (%s); its status is recorded in %s'
              % (run_dir, os.path.basename(target),
                 e, os.path.join(name, META)), flush=True)
        return run_dir
    # the processed twin follows the rename, so a run keeps ONE name
    results_store.rename(name, os.path.basename(target))
    try:
        results_store.mirror(target)
    except Exception as e:                                   # noqa: BLE001
        print('record mirror failed (%s): %s' % (target, e), flush=True)
    return target


def reconcile_stale():
    """Mark as aborted any run that claims to be running under a dead harness.

    A hard kill leaves no chance to update the metadata, so the next harness
    invocation settles it: status `running` with the recorded pid gone means
    the run is dead. A live concurrent arm has a live pid and is left alone.
    """
    for path in (glob.glob(os.path.join(RAW, '*', META))
                 + glob.glob(os.path.join(RESULTS, '*', META))):
        run_dir = os.path.dirname(path)
        try:
            doc = json.load(open(path, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if doc.get('status') != 'running':
            continue
        if doc.get('pid') and _pid_alive(doc['pid']):
            continue
        # 9.165: THE LOG IS ASKED FIRST. A run whose harness died can still
        # have died on its own account - `20260910T222830_300it_25pct` threw
        # OutOfMemoryError in iteration 98 with the harness long gone, and this
        # branch would have headlined "the harness is no longer running" over
        # a JVM that died of a 14 GB heap. If the run's own log records a
        # terminating exception, that is the cause and the status is `failed`;
        # the dead-harness reading is the fallback for a log that ends quietly.
        log_path = os.path.join(run_dir, 'matsim.log')
        died_on_its_own = (run_failure.from_log(log_path)
                           or run_failure._last_error(log_path))
        # The card is filled from the log, not left at None: the F33 arm 0
        # card said `launched: None, reached_iteration: None` while the board
        # printed both (eighth report, 11 September 2026).
        reached = _last_ended_iteration(run_dir)
        wall_s = None
        try:
            t0 = time.mktime(time.strptime(doc.get('started') or '',
                                           '%Y-%m-%dT%H:%M:%S'))
            wall_s = round(max(0.0, os.path.getmtime(log_path) - t0), 1)
        except (TypeError, ValueError, OSError):
            pass
        update_meta(run_dir, reached_iteration=reached if reached >= 0 else None)
        if died_on_its_own:
            dead = mark_dead(run_dir, 'failed', wall_s=wall_s, cause=None)
            print('reconciled: %s claimed to be running under a dead harness, '
                  'and its own log says why it died; marked failed -> %s'
                  % (os.path.basename(run_dir), os.path.basename(dead)),
                  flush=True)
            continue
        dead = mark_dead(run_dir, 'aborted',
                         cause='the harness that launched this run is no longer '
                               'running and the run never reported an end; '
                               'settled by a later harness invocation')
        print('reconciled: %s claimed to be running under a dead harness; '
              'marked aborted -> %s' % (os.path.basename(run_dir),
                                        os.path.basename(dead)), flush=True)


GATE_STOP = '_gate_stop.json'
# The operator's counterpart to GATE_STOP, written by stop_run BEFORE it kills
# anything. Both processes race for the terminal record: --stop kills the JVM,
# and the harness sitting in proc.wait() can wake first, find no marker, and
# record `failed` - renaming the directory out from under the stop, which then
# closes out a run whose card already says something else. With the marker on
# disk before the kill, whichever process gets there writes `aborted` with the
# operator's own words (9.143: a dead run says why, in the words of whoever
# stopped it).
OPERATOR_STOP = '_operator_stop.json'
# The ceiling watcher's marker, written BEFORE the kill for the same
# reason OPERATOR_STOP is (9.143): whichever process reaches the
# terminal record first must find the stated cause already on disk.
CEILING_STOP = '_ceiling_stop.json'
# The stall watcher's marker, written BEFORE the kill for the same reason.
STALL_STOP = '_stall_stop.json'
# the reporter's verdict file, written per milestone and read by the watcher;
# module-level so a test can point the watcher at a canned reporter
GATE_VERDICT = '_gate_verdict.json'
REPORTER = os.path.join(REPO, 'src', 'analyse', 'report_mode_ridership.py')
EXTRACTOR = os.path.join(REPO, 'src', 'analyse', 'extract_metrics.py')


def extract_metrics(run_dir):
    """Write a closed-out run's `_metrics.json`, best effort (9.137, #132).

    `run.py` does this after `run()` returns, for every run that ended at a
    defined boundary. **`--stop` never reaches it**: it kills the harness's own
    pid, so `run()` returns to nobody and `run.py` returns from its `--stop`
    branch long before the extraction. An operator-stopped arm therefore never
    got a `_metrics.json` at all - and that file is exactly what the store's
    trim guard reads to decide a run is out of its extraction window, so every
    such directory was held against the raw cap until 9.155 gave the guard a
    grace to expire. Thirteen directories were in that state on 7 September
    2026. The composition is fixed here rather than by weakening the guard.

    Returns True when the file was written. A failure is REPORTED, never
    raised: the record and the summary are already on disk, the run's findings
    are already mirrored into processed, and metrics can be re-extracted by
    hand. The extractor owns its own CLI contract, so this shells out to it
    exactly as `run.py` does rather than importing it.
    """
    try:
        out = subprocess.run([sys.executable, EXTRACTOR, '--run', run_dir],
                             capture_output=True, text=True, cwd=REPO)
    except (OSError, subprocess.SubprocessError) as e:
        print('metric extraction could not be started (the run itself is '
              'intact): %s' % e, flush=True)
        return False
    if out.stdout:
        print(out.stdout.rstrip(), flush=True)
    if out.returncode != 0:
        print('metric extraction failed (the run itself is intact): rc=%s %s'
              % (out.returncode, (out.stderr or '').strip()[-400:]), flush=True)
        return False
    return True


def _last_ended_iteration(run_dir):
    """The run's newest iteration: the progress digest first, the log tail second.

    The digest (`_progress.json`) scans the log incrementally and cannot miss a
    marker. A fixed 64 KiB tail can: at the 25% arm's log rate the ENDS marker
    is flushed out of the tail within a second of being written (measured 611
    MiB behind EOF on `aborted_20260901T165115_300it_25pct`), which left the
    9.137 gate watcher blind for a whole run. The digest's figure may be an
    iteration that has BEGUN but not ended; the caller already retries a
    milestone whose tables are not written yet, so that is safe.
    """
    try:
        with open(os.path.join(run_dir, '_progress.json'),
                  encoding='utf-8') as fh:
            it = json.load(fh).get('iteration')
        if isinstance(it, int):
            return it
    except (OSError, ValueError):
        pass
    # No digest (the monitor is off, or it has not written yet): read the
    # log INCREMENTALLY through run_view's cached reader (#131) - the first
    # call walks the log once, every later call reads only its growth. The
    # 64 KiB tail this replaced was blind at the 25% log rate.
    log = os.path.join(run_dir, 'matsim.log')
    try:
        import run_view                                   # noqa: PLC0415
        iters = run_view.read_iterations(log)
    except Exception:                                     # noqa: BLE001
        return -1
    return iters[-1][0] if iters else -1


def start_ceiling_watch(run_dir, cfg, proc, t0):
    """Stop the run when its wall clock passes the approved cost (#169).

    A SECOND watcher, deliberately not a branch of the gate's: that one stops
    on a modelling condition and this one on a budget, they carry different
    departures, and `RUN.gate.interval_iterations = 0` must keep meaning "do
    not judge my modes" rather than "do not enforce my budget". The arm that
    exposed the gap disables the gate watcher for a good reason and therefore
    had no automatic stop of any kind.

    `RUN.gate.wall_ceiling_h` = 0 means no ceiling and is the default, so a run
    that does not set one behaves exactly as before. The watcher can only END a
    run, never extend one: it does not read the pace, does not project, and
    does not negotiate - it compares the clock it was given against the number
    the approval named.

    Like the gate watcher it is a daemon and swallows its own failures: a
    watcher that cannot read something must never kill a healthy run.
    """
    try:
        ceiling_h = float(cfg.get('RUN.gate.wall_ceiling_h'))
    except Exception:                                        # noqa: BLE001
        return None
    if ceiling_h <= 0:
        return None
    # an OBSERVER cadence, declared like the gate watcher's retry interval; it
    # bounds only how far past its ceiling a run can get, never the ceiling
    try:
        poll_s = float(cfg.get('RUN.gate.ceiling_poll_s'))
    except Exception:                                        # noqa: BLE001
        poll_s = 60.0
    import threading
    limit_s = ceiling_h * 3600.0

    def loop():
        while proc.poll() is None:
            # checked BEFORE the sleep, so a ceiling already passed at launch
            # stops the run at once rather than one cadence later
            spent = time.time() - t0
            if spent < limit_s:
                time.sleep(poll_s)
                continue
            verdict = dict(stopped=_now(), ceiling_h=ceiling_h,
                           wall_s=round(spent, 1),
                           reached_iteration=_last_ended_iteration(run_dir))
            try:
                with open(os.path.join(run_dir, CEILING_STOP), 'w',
                          encoding='utf-8', newline='\n') as fh:
                    json.dump(verdict, fh, indent=1)
            except OSError:
                pass
            print('ceiling watcher: stopping the run - %.2f h spent against an '
                  'approved ceiling of %.2f h (RUN.gate.wall_ceiling_h)'
                  % (spent / 3600.0, ceiling_h), flush=True)
            proc.kill()
            return

    t = threading.Thread(target=loop, daemon=True, name='ceiling-watch')
    t.start()
    return t


def start_stall_watch(run_dir, cfg, proc, log):
    """Stop the run when its log has gone silent for RUN.gate.stall_kill_s (#66).

    The liveness watcher. `RUN.monitor.stall_s` (300 s) is what the live view
    CALLS a stall and it observes only; this one acts, at a much longer
    silence, because the alternative was measured on 11 September 2026:
    `aborted_20260910T222830_300it_25pct` spent 13.1 h inside iteration 89 on
    an awake machine (Task Scheduler log: ~450 launches, no gap, no sleep),
    the progress digest reported the stall at 05:13, and nothing had the job
    of killing it. The ceiling watcher could not - the overlay carried a 26 h
    ceiling - and the gate watcher needs an iteration to END.

    Silence, not iteration length, is the test: MATSim prints every simulated
    hour of the mobsim and the memory observer prints every minute, so a
    healthy iteration at any fraction never goes quiet for the half hour the
    default names, while a JVM in back-to-back full collections goes quiet
    for hours. Zero disables it. Like the other watchers it is a daemon that
    swallows its own failures and can only END a run.
    """
    try:
        kill_s = float(cfg.get('RUN.gate.stall_kill_s'))
    except Exception:                                        # noqa: BLE001
        return None
    if kill_s <= 0:
        return None
    try:
        poll_s = float(cfg.get('RUN.gate.ceiling_poll_s'))
    except Exception:                                        # noqa: BLE001
        poll_s = 60.0
    import threading

    def loop():
        while proc.poll() is None:
            try:
                silent = time.time() - os.path.getmtime(log)
            except OSError:
                silent = 0.0
            if silent < kill_s:
                time.sleep(poll_s)
                continue
            verdict = dict(stopped=_now(), stall_kill_s=kill_s,
                           silent_s=round(silent, 1),
                           reached_iteration=_last_ended_iteration(run_dir))
            try:
                with open(os.path.join(run_dir, STALL_STOP), 'w',
                          encoding='utf-8', newline='\n') as fh:
                    json.dump(verdict, fh, indent=1)
            except OSError:
                pass
            print('stall watcher: stopping the run - the log has been silent '
                  'for %.0f s against RUN.gate.stall_kill_s = %.0f s, after '
                  'iteration %s' % (silent, kill_s, verdict['reached_iteration']),
                  flush=True)
            proc.kill()
            return

    t = threading.Thread(target=loop, daemon=True, name='stall-watch')
    t.start()
    return t


def start_gate_watch(run_dir, cfg, proc):
    """The GOAL.md loop's hard bar, executed by the runner itself (9.137).

    Every `RUN.gate.interval_iterations` iterations the watcher reads all
    twelve modes with the same reporter a person would use; if any mode is at
    or past the stop bar the run is stopped HERE - the verdict written to
    `_gate_stop.json`, the JVM killed, and run() records the abort with the
    gate table as its cause. A person never kills a run at a gate again; the
    trend half of the loop ('or heading there') stays a session judgement.
    The watcher is a daemon and every failure is swallowed after a retry:
    an unreadable milestone must never kill a healthy run.
    """
    try:
        interval = int(cfg.get('RUN.gate.interval_iterations'))
        # seconds between reporter attempts on a milestone whose tables are
        # not written yet (#131); the milestone itself is never skipped
        retry_s = float(cfg.get('RUN.gate.retry_interval_s'))
    except Exception:                                        # noqa: BLE001
        return None
    if interval <= 0:
        return None
    # 9.164 (#131): RUN.gate SILENTLY DEPENDED ON RUN.monitor, and the
    # dependency was measured rather than argued. On the probe
    # 20260910T205517_20it_1pct the monitor was off, the interval was 2 and the
    # run reached iteration 3: the watcher should have judged at iteration 2
    # and there is no verdict file, no gate line and no warning anywhere in the
    # run. The watcher's own reader needs what the monitor maintains, and its
    # fallback - a 64 KiB tail - was measured 611 MiB behind EOF on a 25% arm.
    # A watcher that arms and judges nothing is worse than one that refuses:
    # the launch banner says the run has an automatic stop, and it has not.
    if not bool(cfg.get('RUN.monitor.enabled')):
        print('      GATE WATCHER NOT ARMED: RUN.gate.interval_iterations is '
              '%d but RUN.monitor.enabled is false, and the watcher reads what '
              'the monitor maintains. This run has NO modelling stop (#131). '
              'Turn the monitor on, or state that the run is deliberately '
              'unjudged beside the approval on its overlay.' % interval,
              flush=True)
        return None
    import threading
    reporter = REPORTER
    verdict_path = os.path.join(run_dir, GATE_VERDICT)

    def loop():
        claimed = 0
        retry_at = 0.0
        while proc.poll() is None:
            time.sleep(30)
            it = _last_ended_iteration(run_dir)
            milestone = (it // interval) * interval if it >= 0 else 0
            if milestone <= claimed:
                continue
            # a milestone whose tables are not written yet is retried at a
            # bounded cadence (#131): the reporter reads the whole trips
            # table, and running it every 30 s against a 25% arm competed
            # with the JVM for the disk
            if time.time() < retry_at:
                continue
            try:
                out = subprocess.run(
                    [sys.executable, reporter, '--run', run_dir,
                     '--it', str(milestone), '--gate-json', verdict_path],
                    capture_output=True, text=True, timeout=1800, cwd=REPO)
            except (OSError, subprocess.SubprocessError):
                retry_at = time.time() + retry_s
                continue
            if out.returncode != 0:
                # table not written yet - retry until the run moves a whole
                # interval past the milestone, then let it go
                if it >= milestone + interval:
                    claimed = milestone
                retry_at = time.time() + retry_s
                continue
            # THE STOP IS KEYED ON THE VERDICT FILE, NEVER ON THE PRINTED
            # TEXT (#112): the reporter prints a `GATE:` line on a pass as
            # well as on a breach, and a substring test would have killed the
            # first arm to clear its bar. A verdict that is missing or from
            # another milestone means the reporter did not speak for this
            # one - retry, never guess.
            try:
                with open(verdict_path, encoding='utf-8') as fh:
                    read = json.load(fh)
            except (OSError, ValueError):
                read = None
            if not isinstance(read, dict) \
                    or read.get('iteration') != milestone:
                if it >= milestone + interval:
                    claimed = milestone
                retry_at = time.time() + retry_s
                continue
            claimed = milestone
            breaches = read.get('breaches') or []
            if read.get('passed') or not breaches:
                print('gate watcher: iteration %d PASSED - no mode at or '
                      'past the stop bar; the run continues'
                      % milestone, flush=True)
                continue
            text = out.stdout
            gate_lines = (text[text.index('GATE:'):].strip().splitlines()
                          if 'GATE:' in text else
                          ['GATE: %d mode(s) at or past the stop bar'
                           % len(breaches)])
            verdict = dict(iteration=milestone,
                           stopped=_now(),
                           interval=interval,
                           breaches=breaches,
                           gate=[ln.strip() for ln in gate_lines])
            try:
                with open(os.path.join(run_dir, GATE_STOP), 'w',
                          encoding='utf-8', newline='\n') as fh:
                    json.dump(verdict, fh, indent=1)
            except OSError:
                pass
            print('gate watcher: stopping the run at iteration %d - %s'
                  % (milestone, gate_lines[0]), flush=True)
            proc.kill()
            return

    t = threading.Thread(target=loop, daemon=True, name='gate-watch')
    t.start()
    return t


def _trim_async(cfg):
    """Trim the raw cache on a daemon thread, after the launch (#132)."""
    import threading

    def go():
        try:
            results_store.trim(cfg.get('RUN.storage.raw_cap_gb'),
                               grace_s=cfg.get('RUN.storage.extract_grace_s'))
        except Exception as e:                               # noqa: BLE001
            print('raw cache trim failed (the run is unaffected): %s' % e,
                  flush=True)
    threading.Thread(target=go, daemon=True, name='raw-trim').start()


def refuse_launch(run_dir, meta, exc):
    """A launch refused before MATSim started still says why (#127).

    The card is written once, already `failed`, with the refusal quoted as
    its cause - the meta contract requires a cause on every dead run - and
    the directory is then retired through `mark_dead`, so it carries the
    `aborted_` label like every other run that did not complete and its
    processed twin follows. The JVM never ran, so there is no log to read;
    the message the launch died with is the only evidence, and it is kept.
    """
    msg = str(exc).strip() or exc.__class__.__name__
    cause = 'launch refused before MATSim started: %s' % msg
    card = dict(meta, status='failed', ended=_now(), wall_s=0.0, rc=None,
                cause=cause)
    try:
        write_meta(run_dir, card)
    except Exception as e:                                   # noqa: BLE001
        print('could not write the refusal card for %s: %s' % (run_dir, e),
              flush=True)
        return run_dir
    print('LAUNCH REFUSED - %s' % cause, flush=True)
    return mark_dead(run_dir, 'failed', wall_s=0.0, cause=cause)


def _gate_stop_cause(run_dir):
    """The cause composed from the watcher's verdict file, or None."""
    path = os.path.join(run_dir, GATE_STOP)
    if not os.path.exists(path):
        return None
    try:
        doc = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    lines = doc.get('gate') or []
    return ('Stopped automatically by the gate watcher at iteration %s under '
            'the GOAL.md loop (RUN.gate.interval_iterations=%s): %s'
            % (doc.get('iteration'), doc.get('interval'),
               ' | '.join(lines[:10])))


def _ceiling_stop_cause(run_dir):
    """The cause composed from the ceiling watcher's marker, or None."""
    path = os.path.join(run_dir, CEILING_STOP)
    if not os.path.exists(path):
        return None
    try:
        doc = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return ('Stopped automatically by the ceiling watcher at %.2f h against an '
            'approved ceiling of %s h (RUN.gate.wall_ceiling_h), at iteration '
            '%s. The run is citable at that iteration and nowhere past it; it '
            'is NOT a complete arm (9.143, #169).'
            % ((doc.get('wall_s') or 0) / 3600.0, doc.get('ceiling_h'),
               doc.get('reached_iteration')))


def _stall_stop_cause(run_dir):
    """The cause composed from the stall watcher's marker, or None."""
    path = os.path.join(run_dir, STALL_STOP)
    if not os.path.exists(path):
        return None
    try:
        doc = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return ('Stopped automatically by the stall watcher: the log was silent for '
            '%s s against RUN.gate.stall_kill_s = %s s, after iteration %s. The '
            'run is citable at that iteration and nowhere past it; it is NOT a '
            'complete arm. Read gc.log for the collector\'s account (#66).'
            % (doc.get('silent_s'), doc.get('stall_kill_s'),
               doc.get('reached_iteration')))


def _operator_stop_cause(run_dir):
    """The cause the operator gave to `--stop`, read from its marker, or None."""
    path = os.path.join(run_dir, OPERATOR_STOP)
    if not os.path.exists(path):
        return None
    try:
        doc = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return doc.get('cause') or None


def _stop_marker(run_dir):
    """(cause, completion) for a run stopped at a DEFINED BOUNDARY, or (None, None).

    Consulted by the harness's terminal path so that a killed JVM is never
    recorded as a crash when somebody or something stopped it deliberately.
    """
    gate = _gate_stop_cause(run_dir)
    if gate:
        return gate, STOPPED_AT_GATE
    # The gate is read first because a modelling breach says more about the
    # model than a budget does; a run that hit both is described by the more
    # informative boundary. The operator is read last because a person who
    # stopped a run already knows why.
    ceiling = _ceiling_stop_cause(run_dir)
    if ceiling:
        return ceiling, STOPPED_AT_CEILING
    stall = _stall_stop_cause(run_dir)
    if stall:
        return stall, STOPPED_AT_STALL
    op = _operator_stop_cause(run_dir)
    if op:
        return ('Stopped by the operator through run.py --stop: %s' % op,
                STOPPED_BY_OPERATOR)
    return None, None


def close_out(run_dir, completion, rc, wall_s, reached_iteration=None,
              stop_cause=None, extra=None, cfg=None):
    """Write a run's record and summary at whichever boundary ended it.

    THE RECORD USED TO BE WRITTEN ON rc=0 ALONE, so a run stopped at a GOAL.md
    gate left a directory holding a real reading and nothing that could cite it.
    Every arm since family F4 stopped before its horizon, and each one reached
    the next session as an orphan whose figures had to be re-derived from a 51
    GiB log. A run that ends at a DEFINED boundary now closes itself out.

    What the record's presence means is therefore narrower than it was, and the
    field carries the difference: presence means THIS RUN CAN BE CITED, and only
    `completion == RAN_TO_LAST` means it ran the horizon it declared. Resume
    matching (`find_completed`) and the calibrated base both ask the field, so a
    stopped arm can never be handed back as a finished one.

    A CRASH STILL WRITES NOTHING. A run that died of an exception has no
    boundary and no defensible reading, and manufacturing a record for it would
    turn this from a close-out into a green light - the one failure the run
    index exists to prevent.

    Every step is best-effort and reported, never raised: the run has already
    ended, and a summary that cannot be written must not also destroy the record
    that can.
    """
    name = os.path.basename(run_dir)
    meta = _load_meta(run_dir)
    if not meta:
        print('cannot close out %s: no %s to build a record from'
              % (name, META), flush=True)
        return None
    if wall_s is None:
        # --stop kills the harness that was holding the clock, so the elapsed
        # time is taken from the card's own launch stamp rather than left at
        # zero: a stopped arm's wall clock is the cost it actually spent.
        wall_s = _elapsed_since(meta.get('started'))
    per = iteration_times(os.path.join(run_dir, 'matsim.log'))
    steady = sorted(v for k, v in per.items() if k > 0)
    if reached_iteration is None:
        # THE LAST ITERATION THAT ENDED - never the one in flight. `per` holds
        # an iteration only once its ENDS marker is read, which is the property
        # this needs; `_last_ended_iteration` does NOT have it. That reader
        # takes the progress digest's figure, which is an iteration that has
        # BEGUN - safe for the gate watcher, which simply retries until the
        # milestone's tables appear, but WRONG in a record, where it would
        # claim the run reached an iteration whose tables were never written
        # and send a reader to a milestone that holds nothing.
        #
        # Measured on the first arm ever closed out this way
        # (20260904T181203_300it_25pct): stopped while iteration 100 was in
        # flight, the digest said 100, and the newest readable milestone was
        # 90. The record said 100 until this used the ENDS markers instead.
        reached_iteration = max(per) if per else _last_ended_iteration(run_dir)
    doc = dict(name=name,
               scenario=meta.get('scenario'), day=meta.get('day'),
               fraction=meta.get('fraction'), iterations=meta.get('iterations'),
               threads=meta.get('threads'), xmx=meta.get('xmx'),
               seed=meta.get('seed'), overrides=meta.get('overrides') or {},
               rc=rc, wall_s=round(wall_s, 1) if wall_s is not None else 0.0,
               median_iteration_s=steady[len(steady) // 2] if steady else None,
               completion=completion,
               reached_iteration=reached_iteration,
               stop_cause=stop_cause,
               controler_sha256=meta.get('controler_sha256'),
               values_sha256=meta.get('values_sha256'),
               inputs_sha256=meta.get('inputs_sha256'),
               **(meta.get('sample') or {}))
    if meta.get('config_snapshot'):
        doc['config_snapshot'] = meta['config_snapshot']
    if meta.get('warm_started_from'):
        doc['warm_started_from'] = meta['warm_started_from']
    doc.update(extra or {})
    try:
        outputs.write_checked(os.path.join(run_dir, '_run.json'), doc, 'run')
    except outputs.OutputError as e:
        # On the success path the caller turns this into a refusal; on a stop
        # path the reading still exists and the meta card still states the
        # cause, so a rejected record is reported and the close-out continues.
        print('run record could not be written for %s: %s' % (name, e),
              flush=True)
        return None
    # `_summary.json` against its declared schema and `SUMMARY.md` for a person.
    # It reports the state of the RUN and refuses to report a finding: no mode
    # share, no fit statistic, no validation target.
    try:
        summarise_run.summarise(run_dir)
    except Exception as e:                                   # noqa: BLE001
        print('summary could not be written: %s' % e, flush=True)
    # findings into processed and the cache back under budget, unattended
    # (9.137) - a closed-out run's readings survive any later trim
    try:
        results_store.process(name, extract=True)
        if cfg is not None:
            results_store.trim(cfg.get('RUN.storage.raw_cap_gb'),
                               grace_s=cfg.get('RUN.storage.extract_grace_s'))
    except Exception as e:                                   # noqa: BLE001
        print('post-run processing failed: %s' % e, flush=True)
    return doc


def _load_meta(run_dir):
    try:
        return json.load(open(os.path.join(run_dir, META), encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _elapsed_since(started):
    """Seconds from a card's `started` stamp to now; 0.0 if it cannot be read."""
    try:
        t0 = time.mktime(time.strptime(started, '%Y-%m-%dT%H:%M:%S'))
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, time.time() - t0)


def stop_run(name, cause):
    """Stop a running arm through the harness - never by hand (9.137).

    Ends the run's scheduled task if one exists, kills the recorded process
    tree, and records the abort with the caller's cause. The one sanctioned
    way a person (or a session) stops a run.
    """
    run_dir = results_store.resolve(name)
    if run_dir is None:
        raise SystemExit('no run named %s' % name)
    meta = json.load(open(os.path.join(run_dir, META), encoding='utf-8'))
    if meta.get('status') != 'running':
        raise SystemExit('%s is not running (status %s)'
                         % (name, meta.get('status')))
    # THE MARKER GOES DOWN BEFORE ANYTHING DIES. Whoever writes the terminal
    # record - this process, or the harness waking out of proc.wait() when the
    # JVM dies - then finds the operator's own cause and records `aborted`
    # rather than `failed`.
    try:
        with open(os.path.join(run_dir, OPERATOR_STOP), 'w',
                  encoding='utf-8', newline='\n') as fh:
            json.dump(dict(cause=cause, at=_now()), fh, indent=1)
    except OSError:
        pass
    # THE HARNESS DIES FIRST, THEN THE JVM. Killing the JVM first woke the
    # harness out of proc.wait() into its own terminal path, where it renamed
    # the directory - so the stop below then closed out a directory that had
    # moved. The jvm pid is still killed after, because on POSIX killing the
    # harness alone left the JVM running (#128); on Windows /T takes the tree
    # and the second kill is a no-op.
    for victim in (meta.get('pid'), meta.get('jvm_pid')):
        if not victim:
            continue
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/PID', str(victim), '/T'],
                           capture_output=True)
        else:
            subprocess.run(['kill', '-9', str(victim)], capture_output=True)
    time.sleep(3)
    # The harness may have written the terminal record and renamed the
    # directory before it died; re-resolve so this close-out targets the run
    # where it actually is.
    run_dir = results_store.resolve(name) or run_dir
    dead = mark_dead(run_dir, 'aborted', cause=cause)
    # THE STOP IS A BOUNDARY, NOT A DEATH, so the run is closed out here rather
    # than left as a directory. It has to happen in THIS process: --stop kills
    # the harness's own pid as well as the JVM, so the harness never unwinds to
    # write anything. The reading up to `reached_iteration` is real; the record
    # says `stopped_by_operator`, so nothing can mistake it for a finished arm.
    doc = close_out(dead, STOPPED_BY_OPERATOR, rc=None,
                    wall_s=meta.get('wall_s'), stop_cause=cause)
    print('stopped and recorded: %s%s'
          % (os.path.basename(dead),
             (' (closed out at iteration %s)' % doc.get('reached_iteration'))
             if doc else ''), flush=True)
    # AND THEN THE SAME MATERIALS THE HARNESS PATH PRODUCES. A stop is a
    # boundary, not a death, so it ends where `run.py` ends a run that returned
    # to it: metrics extracted from the closed-out directory, the file mirrored
    # into processed, and the raw cache trimmed back under its budget. Only the
    # record is a precondition - the extractor reads `_run.json` for the run's
    # identity and its `reached_iteration` - so a close-out that wrote none
    # leaves the bulk to the store's grace rather than being extracted blind.
    if doc is not None:
        extract_metrics(dead)
        results_store.mirror(dead)
    try:
        cfg = registry.load()
        results_store.trim(cfg.get('RUN.storage.raw_cap_gb'),
                           grace_s=cfg.get('RUN.storage.extract_grace_s'))
    except Exception as e:                                   # noqa: BLE001
        print('raw cache trim failed (the stop is recorded): %s' % e,
              flush=True)
    return dead


def run(scenario, day, cfg, overrides, force=False, warm=None,
        registry_overrides=None):
    src_dir = os.path.join(SETS, scenario, day)
    if not os.path.isdir(src_dir):
        raise SystemExit('no run inputs at %s' % src_dir)
    reconcile_stale()
    # the store maintains itself at every harness start: migrate anything
    # legacy now; the raw cache is trimmed back under its declared budget on
    # a daemon thread once the run is launched (#132 - at 671 GiB against a
    # 500 GB cap the synchronous trim held the launch for the deletion)
    try:
        moved = results_store.migrate()
        if moved:
            print('results store: migrated %d run(s) under results/raw'
                  % len(moved), flush=True)
    except Exception as e:                                   # noqa: BLE001
        print('results store migration failed (continuing): %s' % e,
              flush=True)

    fraction = cfg.get('RUN.sample.fraction')
    try:
        iterations = cfg.get('RUN.controler.last_iteration')
    except registry.RegistryError as e:
        raise SystemExit('%s\n\nSet it with --iterations N, --set '
                         'RUN.controler.last_iteration=N, or a run overlay.' % e)
    threads = cfg.get('RUN.machine.threads')
    xmx = cfg.get('RUN.machine.xmx')
    seed = cfg.get('RUN.machine.seed')
    jfr = bool(cfg.get('RUN.machine.jfr_profile'))
    gc_log = bool(cfg.get('RUN.machine.gc_log'))
    announce_cost(iterations, fraction, cfg)
    refuse_if_no_automatic_stop(cfg)
    refuse_small_heap(cfg, xmx, fraction)
    print('heap: -Xmx%s against the registry rule\'s %.1f GiB at a %.2f sample; '
          'GC log %s (RUN.machine.gc_log)'
          % (xmx, heap_floor_gib(cfg, fraction), float(fraction),
             'ON' if gc_log else 'OFF'), flush=True)

    warm_key = None
    if warm is not None:
        check_warm_compatibility(warm, scenario, day, fraction, seed, threads,
                                 overrides)
        warm_key = dict(run=warm['run'], iteration=warm['iteration'])
        print('warm start: continuing %s from its iteration-%d plans '
              '(firstIteration=%d). A warm-started run is NOT bit-identical '
              'to an uninterrupted one - see DECISIONS.md 9.76.'
              % (warm['run'], warm['iteration'], warm['iteration']), flush=True)

    controler = controler_sha256()
    values = values_sha256(cfg)
    inputs = inputs_sha256(day)
    prior = find_completed(scenario, day, fraction, iterations, seed, overrides,
                           controler, warm_key, values, inputs)
    if prior is not None and not force:
        if prior.get('controler_sha256') == controler:
            print('resume: %s already complete' % prior['name'], flush=True)
            return prior
        # A run's parameters cannot see the controler's own source. Without
        # this check a completed run would be handed back after the model's
        # behaviour had changed - silently, and with no way to tell the two
        # apart afterwards. Issue #28 changed how `ride` gets its travel time
        # and moved every mode share, so a stale result reused here would be
        # indistinguishable from a real one. The stale directory is left in
        # place - deleting a result is never this script's call.
        print('re-running: %s has the same parameters but a changed controler\n'
              '  recorded %s\n  current  %s'
              % (prior['name'], (prior.get('controler_sha256') or 'not recorded')[:16],
                 controler[:16]), flush=True)

    # The RUNNER names the directory: launch stamp + iterations + sample
    # percentage. The stamp is a label for humans sorting `results/`; run
    # identity is the parameter set matched above.
    stamp = time.strftime('%Y%m%dT%H%M%S')
    name = '%s_%dit_%spct' % (stamp, iterations, '%g' % (fraction * 100))
    n = 2
    while os.path.exists(results_store.raw_dir(name)) \
            or os.path.exists(os.path.join(RESULTS, name)):
        name = '%s_%dit_%spct-%d' % (stamp, iterations, '%g' % (fraction * 100), n)
        n += 1
    run_dir = results_store.raw_dir(name)
    record = os.path.join(run_dir, '_run.json')
    os.makedirs(run_dir, exist_ok=True)
    # The status card, written at LAUNCH and updated at every transition, so a
    # run can be observed - and considered or disregarded - without opening a
    # log. It is not the result gate: `_run.json`, written only on success,
    # stays that.
    meta = dict(
        status='running', scenario=scenario, day=day, fraction=fraction,
        sample_pct=float('%g' % (fraction * 100)), iterations=iterations,
        seed=seed, threads=threads, xmx=xmx, overrides=overrides or {},
        controler_sha256=controler, inputs_sha256=inputs,
        started=_now(), ended=None, wall_s=None,
        rc=None, pid=os.getpid())
    if warm_key:
        meta['warm_started_from'] = warm_key

    # THE INPUTS ARE VALIDATED BEFORE THE CARD SAYS `running` (#127): a
    # missing input file, a regime mismatch or an unbuilt run stack refuses
    # the launch here, and the refusal is written to the card as the cause -
    # `failed`, with the message quoted. The card used to be written first,
    # so a refused launch left a `running` record that the next harness
    # reconciled as "no longer running" and the real message was lost.
    try:
        # `iterations`, `threads` and every other declared value reach the
        # config through `cfg`, not through this call: they are registry
        # fields, and the emitter reads them from the same resolution the
        # snapshot records.
        config_path, sample = build_config(src_dir, run_dir, scenario, day,
                                           fraction, seed, overrides, cfg,
                                           warm=warm)
        snapshot = cfg.write_snapshot(os.path.join(run_dir, '_config.json'))
        # THE STACK FOLLOWS THE REPRESENTATION (#73, DECISIONS 9.73/9.76):
        # the signals contrib is not in the shaded jar and must never share
        # a classpath with it, so an explicit-signals run executes the
        # Maven-built run stack and the signals entry point; everything else
        # runs exactly the stack it always ran.
        main_class = MAIN
        if cfg.get('A.signals.representation') == 'explicit_signals':
            stack_jars = sorted(glob.glob(os.path.join(
                REPO, '.tools', 'run-stack', 'lib', '*.jar')))
            classes_signals = os.path.join(REPO, '.tools', 'classes-signals')
            if not stack_jars or not os.path.isdir(classes_signals):
                raise SystemExit(
                    'A.signals.representation is explicit_signals but the '
                    'signals run stack is not built. Run: python '
                    'src/setup/bootstrap_toolchain.py --run-stack')
            classpath = os.pathsep.join([classes_signals] + stack_jars)
            main_class = 'citysim.CitysimSignalsControler'
        else:
            classpath = os.pathsep.join([JAR, CLASSES])
    except (SystemExit, Exception) as e:                     # noqa: BLE001
        refuse_launch(run_dir, meta, e)
        raise
    # THE CARD CARRIES EVERYTHING THE RECORD WILL NEED. A run stopped at a gate
    # is closed out by whichever process survives the stop - this harness for a
    # gate stop, `--stop`'s own process for an operator stop - and neither can
    # reach the locals build_config() just produced. Stashing them on the card
    # at launch is what lets a stopped run state its identity as completely as a
    # run that reached its horizon, instead of leaving a directory that can only
    # be re-derived from a log.
    meta.update(
        config_snapshot=os.path.relpath(snapshot, run_dir).replace(os.sep, '/'),
        values_sha256=values, sample=sample)
    write_meta(run_dir, meta)
    log = os.path.join(run_dir, 'matsim.log')
    # -Xms equal to -Xmx: the 9.57 arm grew the heap 7 -> 27 GB across the run
    # with full-GC stalls visible during the it-110 routing pathology; a
    # pre-sized heap removes the growth path. Wall-time only - the JVM heap
    # schedule cannot change a model output.
    cmd = [JAVA, '-Xms%s' % xmx, '-Xmx%s' % xmx, '-XX:+UseParallelGC']
    # OBSERVATION ONLY (RUN.machine.jfr_profile, RUN.machine.gc_log). Neither
    # flag reaches MATSim: JFR samples the stacks of threads that are running
    # anyway and GC logging prints what the collector already did, so a
    # profiled run and an unprofiled one are the same run. They are declared
    # rather than typed here because the launcher's flag list is a set of
    # values a script was deciding on its own.
    if jfr:
        cmd.append(
            '-XX:StartFlightRecording=settings=profile,disk=true,'
            'dumponexit=true,maxsize=2g,filename=%s'
            % os.path.join(run_dir, 'profile.jfr'))
    if gc_log:
        cmd.append('-Xlog:gc*:file=%s:time,uptime,level,tags'
                   % os.path.join(run_dir, 'gc.log').replace('\\', '/'))
    cmd += ['-cp', classpath, main_class, config_path]
    # The live view, announced before MATSim starts so the url is on screen for
    # the whole run rather than after it. It reads the run directory and never
    # writes to it.
    view_url = start_live_view(run_dir, cfg)
    print('live view: %s' % (view_url or 'disabled (RUN.monitor.enabled)'),
          flush=True)
    # The machine-readable digest, refreshed beside the live view so an agent
    # or a script reads ONE file (_progress.json) instead of matsim.log.
    start_progress_digest(run_dir, cfg)
    t0 = time.time()
    try:
        with open(log, 'w', encoding='utf-8', errors='replace') as lf:
            proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT,
                                    cwd=run_dir)
            # the JVM's pid on the card, so --stop can reach it (#128)
            update_meta(run_dir, jvm_pid=proc.pid)
            _trim_async(cfg)
            # the runner gates its own run every RUN.gate.interval_iterations
            # (9.137): a failing hard bar stops the JVM from inside
            start_gate_watch(run_dir, cfg, proc)
            # and the runner enforces its own approved cost (#169): the gate
            # watcher stops on a modelling condition and knows nothing about
            # clocks, so an arm that disables it had no automatic stop at all
            start_ceiling_watch(run_dir, cfg, proc, t0)
            # and it refuses to hold the machine for a JVM that has stopped
            # writing (#66): the third watcher, on liveness
            start_stall_watch(run_dir, cfg, proc, log)
            rc = proc.wait()
    except BaseException:
        # Ctrl+C or a harness kill that still unwinds: record the abort and
        # rename before propagating. A kill this except cannot see is settled
        # by reconcile_stale() on the next invocation.
        mark_dead(run_dir, 'aborted', wall_s=round(time.time() - t0, 1),
                  cause='the harness was interrupted before MATSim returned '
                        '(Ctrl+C, or a kill this process still unwound)')
        raise
    wall = time.time() - t0
    if rc != 0:
        gate_cause, completion = _stop_marker(run_dir)
        dead = mark_dead(run_dir, 'aborted' if gate_cause else 'failed',
                         rc=rc, wall_s=round(wall, 1), cause=gate_cause)
        print(('%s after %.0fs - %s'
               % ({STOPPED_AT_GATE: 'GATE-STOPPED',
                   STOPPED_AT_CEILING: 'CEILING-STOPPED',
                   STOPPED_AT_STALL: 'STALL-STOPPED'}.get(
                       completion, 'STOPPED BY THE OPERATOR'),
                  wall, gate_cause))
              if gate_cause else
              ('FAILED rc=%d after %.0fs - see %s'
               % (rc, wall, os.path.join(dead, 'matsim.log'))), flush=True)
        if gate_cause:
            # A GATE STOP IS A BOUNDARY THE LOOP ASKED FOR, so the arm is closed
            # out with the same materials a run that reached its horizon gets:
            # its reading at `reached_iteration` is exactly what the gate was
            # for, and it stops being an orphan the next session must re-derive.
            # The record says `stopped_at_gate`, so it can never be handed back
            # as a finished arm.
            doc = close_out(dead, completion, rc=rc, wall_s=wall,
                            stop_cause=gate_cause, cfg=cfg)
            if doc is not None:
                print('closed out at iteration %s: %s'
                      % (doc.get('reached_iteration'),
                         os.path.join(dead, '_run.json')), flush=True)
                return doc
        # A CRASH GETS NO RECORD - it has no boundary and no defensible reading.
        # Its findings are still extracted while its bulk is fresh, and the
        # cache re-trimmed, both unattended (9.137).
        try:
            results_store.process(os.path.basename(dead), extract=True)
            results_store.trim(cfg.get('RUN.storage.raw_cap_gb'),
                               grace_s=cfg.get('RUN.storage.extract_grace_s'))
        except Exception as e:                               # noqa: BLE001
            print('post-run processing failed: %s' % e, flush=True)
        return dict(name=os.path.basename(dead), rc=rc, wall_s=round(wall, 1))
    update_meta(run_dir, status='completed', ended=_now(), rc=0,
                wall_s=round(wall, 1))

    per = iteration_times(log)
    steady = sorted(v for k, v in per.items() if k > 0)
    doc = dict(name=name, scenario=scenario, day=day, fraction=fraction,
               iterations=iterations, threads=threads, xmx=xmx, seed=seed,
               overrides=overrides,
               # The RAW `--set` channel above and the REGISTRY `--config-set`
               # channel here are different things, and the record now says so.
               # `values_sha256` already fingerprints every resolved value, so
               # run identity was never wrong; what was missing is legibility -
               # neither a reader nor the calibration loop could see WHICH
               # declared values a run moved without re-resolving its overlay.
               registry_overrides=dict(registry_overrides or {}),
               rc=rc, wall_s=round(wall, 1),
               median_iteration_s=steady[len(steady) // 2] if steady else None,
               # The run executed every iteration it declared. That is NOT a
               # claim of convergence - 9.7 holds that separately - and it is
               # the only completion resume matching and the calibrated base
               # accept.
               completion=RAN_TO_LAST, reached_iteration=iterations,
               stop_cause=None,
               config_snapshot=os.path.relpath(snapshot, run_dir).replace(os.sep, '/'),
               controler_sha256=controler,
               values_sha256=values,
               inputs_sha256=inputs,
               **sample)
    if warm_key:
        doc['warm_started_from'] = warm_key
    # The run record must meet its declared contract before it is written; a
    # completed run without a config snapshot cannot state what produced it.
    try:
        outputs.write_checked(record, doc, 'run')
    except outputs.OutputError as e:
        raise SystemExit(str(e))
    print('%s rc=0 wall=%.0fs median iteration %.1fs'
          % (name, wall, doc['median_iteration_s'] or -1), flush=True)
    # A finished run should not leave its telemetry, its log and three JSON files
    # for someone to interpret. Close it out with a summary in both dialects -
    # `_summary.json` against its declared schema, and `SUMMARY.md` for a person.
    # It reports the state of the RUN and refuses to report a finding: no mode
    # share, no fit statistic, no validation target. A failure here is logged and
    # never raised, because the run itself succeeded and its record is written.
    try:
        summarise_run.summarise(run_dir)
    except Exception as e:                                   # noqa: BLE001
        print('summary could not be written: %s' % e, flush=True)
    # findings into processed and the cache back under budget, unattended
    # (9.137) - a completed run's readings survive any later trim
    try:
        results_store.process(name, extract=True)
        results_store.trim(cfg.get('RUN.storage.raw_cap_gb'),
                               grace_s=cfg.get('RUN.storage.extract_grace_s'))
    except Exception as e:                                   # noqa: BLE001
        print('post-run processing failed: %s' % e, flush=True)
    return doc


def parse_override(s):
    key, _, value = s.partition('=')
    if not value:
        raise SystemExit('override must be key=value, got %r' % s)
    return key, value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    # the scenario default and day vocabulary come from city.json - a CLI
    # that hardwired one city's S2/WEEKDAY rejected another city's declared
    # day types outright
    _desc = city.descriptor()
    ap.add_argument('--scenario',
                    default=_desc['intervention']['base_scenario'])
    ap.add_argument('--day', default=list(_desc['day_types'])[0],
                    choices=list(_desc['day_types']))
    ap.add_argument('--run-config', metavar='TAG',
                    help='a committed overlay under config/runs/<TAG>.json - the '
                         'reproducible way to vary a run')
    ap.add_argument('--fraction', type=float,
                    help='shorthand for --set RUN.sample.fraction=...')
    ap.add_argument('--iterations', type=int,
                    help='shorthand for --set RUN.controler.last_iteration=... . '
                         'There is still no default: DECISIONS.md 9.7 shows 100 and '
                         '250 are both too low, no justified value has been measured, '
                         'and the registry declares the field UNOBTAINED so it refuses '
                         'to invent one')
    ap.add_argument('--threads', type=int,
                    help='shorthand for --set RUN.machine.threads=...')
    ap.add_argument('--xmx', help='shorthand for --set RUN.machine.xmx=...')
    ap.add_argument('--seed', type=int, help='shorthand for --set RUN.machine.seed=...')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--warm-start', metavar='DEAD_RUN_DIR',
                    help='continue a crashed run from its newest written plans '
                         'checkpoint (output/ITERS/it.N). Starts a NEW '
                         'runner-named run with firstIteration aligned to the '
                         'checkpoint; the provenance link is recorded as '
                         'warm_started_from. NOT bit-identical to an '
                         'uninterrupted run (DECISIONS.md 9.76)')
    ap.add_argument('--config-set', action='append', default=[], metavar='KEY=VALUE',
                    help='registry override, e.g. RUN.sample.fraction=0.10. Checked '
                         'against the declared sweep; a held-fixed field is refused')
    ap.add_argument('--set', action='append', default=[], metavar='KEY=VALUE',
                    help='MATSim config override; "ride.constant=-3.4" targets a '
                         'modeParams block, "brainExpBeta=2" a plain param')
    a = ap.parse_args()

    # the convenience flags are shorthand for registry overrides, so they go
    # through exactly the same sweep and held-fixed guards as everything else
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
        warm = resolve_warm_start(a.warm_start)
        # firstIteration AND the innovation fraction, derived so the cutoff
        # iteration is the parent's; through the registry's set layer, so it
        # is validated, recorded in _config.json and reaches the config.
        overrides = warm_start_overrides(warm, overrides, a.scenario, a.day,
                                         a.run_config)

    cfg = resolve(a.scenario, a.day, a.run_config, overrides)
    run(a.scenario, a.day, cfg, dict(parse_override(s) for s in a.set), a.force,
        warm=warm, registry_overrides=overrides)


if __name__ == '__main__':
    main()
