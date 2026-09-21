"""Re-emit a finished run's config through the CURRENT emitter and diff it.

    python src/run/reemit_config.py --run <name or path>

A harness or emitter change is verified the way a builder change is (9.203):
regenerate the reference artefact and diff it against the committed one. For
the run harness the artefact is the emitted `config.xml`, and the reference is
a run on disk: this resolves the run's own scenario, day and overlay from its
`_config.json` snapshot, takes the paths its config named, emits again through
`build_matsim_run_inputs.config_runtime` and `param_config.emit`, and prints
either IDENTICAL or the unified diff. A difference is a declared change or a
regression, and the diff says which parameter (9.204: the launcher fold was
proven on the Newcastle 1 % smoke `20260921T180105_2it_1pct` this way - one
line, `hiredFleet.representation = absent`, the new gate's own default).

Nothing is executed and nothing under `results/` is written.
"""
import argparse
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'setup'))
import install_paths                                              # noqa: E402
install_paths.activate(persist=False)

import build_matsim_run_inputs as bi                              # noqa: E402
from registry import param_config                                 # noqa: E402
import results_store                                              # noqa: E402
import run_matsim                                                 # noqa: E402

PATH_PARAMS = (('output', 'controler', 'outputDirectory'),
               ('network', 'network', 'inputNetworkFile'),
               ('plans', 'plans', 'inputPlansFile'),
               ('schedule', 'transit', 'transitScheduleFile'),
               ('vehicles', 'transit', 'vehiclesFile'),
               ('mode_vehicles', 'vehicles', 'vehiclesFile'),
               ('parking_prices', 'parking', 'priceFile'),
               ('signal_systems', 'signalsystems', 'signalsystems'),
               ('signal_groups', 'signalsystems', 'signalgroups'),
               ('signal_control', 'signalsystems', 'signalcontrol'),
               ('change_events', 'network', 'inputChangeEventsFile'),
               ('boarding_fares', 'boardingFare', 'tableFile'))


def param(text, module, name):
    m = re.search(r'<module name="%s">.*?<param name="%s" value="([^"]*)"'
                  % (re.escape(module), re.escape(name)), text, re.S)
    return m.group(1) if m else None


def reemit(run_dir):
    """(reference text, re-emitted text) for one run directory."""
    meta = json.load(open(os.path.join(run_dir, '_meta.json'), encoding='utf-8'))
    snap = json.load(open(os.path.join(run_dir, '_config.json'), encoding='utf-8'))
    overlay = None
    for layer in snap.get('layers', []):
        if str(layer).startswith('run:'):
            overlay = str(layer).split(':', 1)[1]
    cfg = run_matsim.resolve(meta['scenario'], meta['day'], overlay, {})
    text = open(os.path.join(run_dir, 'config.xml'), encoding='utf-8').read()
    paths = dict(fraction=cfg.get('RUN.sample.fraction'))
    for key, module, name in PATH_PARAMS:
        value = param(text, module, name)
        if value is not None:
            paths[key] = value
    if cfg.get('B.hired_fleet.representation') == 'pooled_queue':
        # the derivation lives beside the scenario network, not in the config
        paths['hired_fleet'] = os.path.join(run_matsim.SETS, meta['scenario'], 'hired_fleet.json')
    scoring = bi.c1_scoring(cfg, run_matsim.purpose_share_for(cfg))
    runtime = bi.config_runtime(cfg, scoring, meta['day'], paths)
    return text, param_config.emit('matsim', cfg, runtime)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', required=True, help='a finished run: its name or directory')
    a = ap.parse_args(argv)
    run_dir = results_store.resolve(a.run)
    if run_dir is None:
        raise SystemExit('no run directory for %r' % a.run)
    reference, emitted = reemit(run_dir)
    if reference == emitted:
        print('IDENTICAL: the current emitter reproduces %s byte for byte (%d bytes)'
              % (os.path.basename(run_dir), len(reference)))
        return 0
    diff = list(difflib.unified_diff(reference.splitlines(), emitted.splitlines(),
                                     'reference ' + os.path.basename(run_dir), 'current emitter',
                                     lineterm='', n=1))
    print('DIFFERS in %d diff line(s):' % len(diff))
    print('\n'.join(diff))
    return 1


if __name__ == '__main__':
    sys.exit(main())
