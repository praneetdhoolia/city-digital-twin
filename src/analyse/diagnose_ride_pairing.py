#!/usr/bin/env python
"""Why a DECLARED ride pair failed to pair, leg by leg.

`ride_pairing.csv` counts the misses but cannot say what the declared driver was
actually doing when the pairing was refused. It reports `miss_endpoints`,
`miss_window`, `miss_capacity` and `miss_no_candidate` as totals, and at the
last gate `miss_endpoints` was 27,807 against 4,981 and 1,432 for the other two
- so the number that matters is the one with no explanation attached.

This reads the SAME artefact the engine reads: the selected plans at
`BeforeMobsim`, where a ride leg is still a ride leg. (The realised legs table
cannot answer the question, because `ridePairing.remodeUnpaired` converts every
unpaired ride leg BEFORE the mobsim, so an unpaired ride never appears there -
DECISIONS.md 9.92.)

For each ride leg whose person carries a `boundDriver`, it asks what that
declared driver's plan contains, and classifies the refusal:

    paired_ok            a car leg with both endpoints and inside the window
    window_only          both endpoints match, the clock does not
    dest_only            the driver reaches the passenger's destination from
                         somewhere else - the drop-off an escort actually is
    origin_only          the driver leaves from the passenger's origin and goes
                         somewhere else
    neither_endpoint     the driver made a car trip, but not this one
    driver_no_car_leg    the declared driver is not driving at all this iteration
    no_declared_driver   the demand never named one

The split between `dest_only` and `neither_endpoint` is the whole point: the
first is a rule question and the second is a coherence question, and
`ride_pairing.csv` puts both in `miss_endpoints`.

    python src/analyse/diagnose_ride_pairing.py --run <run dir> --it 100

Reads the run directory only. Writes nothing. **Nothing here is a result.**
"""

import os as _os
import sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..'), _os.path.join(_HERE, '..', 'calibrate')):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import gzip
import re
import json
import time
import argparse
import collections

import registry as _registry                                      # noqa: E402

CONFIG_RE = re.compile(
    r'name="(boundWindowMinutes|pairingWindowMinutes|maxPassengersPerVehicle)"'
    r'\s+value="([^"]*)"')


def windows_from_run(run_dir):
    """The tolerances THIS RUN executed, from its own emitted config.

    Reading them from the live registry instead is a real defect and it was
    committed once: a historical arm then gets re-classified under today's
    rule, and the reclassification looks exactly like a model improvement. The
    first comparison built on this tool showed a 30-minute arm reporting a
    minimum gap of 60.1 - the current window printing itself into an arm that
    never ran it (DECISIONS.md 9.97).
    """
    cfg = _os.path.join(run_dir, 'config.xml')
    if not _os.path.exists(cfg):
        raise SystemExit(
            'no config.xml in %s. The pairing tolerances must come from the '
            'run that executed them, not from the registry as it stands now.'
            % run_dir)
    found = dict(CONFIG_RE.findall(open(cfg, encoding='utf-8').read()))
    if 'boundWindowMinutes' not in found:
        raise SystemExit(
            '%s declares no ridePairing.boundWindowMinutes; this run predates '
            'the declared bound window and cannot be classified by it.' % cfg)
    return found

PERSON_RE = re.compile(r'<person id="([^"]+)"')
ATTR_RE = re.compile(r'<attribute name="([^"]+)"[^>]*>([^<]*)</attribute>')
SELECTED_RE = re.compile(r'<plan[^>]*selected="yes"')
PLAN_END_RE = re.compile(r'</plan>')
LEG_RE = re.compile(r'<leg mode="([^"]+)"(?:[^>]*trav_time="([^"]*)")?[^>]*>')
DEP_RE = re.compile(r'dep_time="([^"]*)"')
ROUTE_RE = re.compile(r'<route type="[^"]*" start_link="([^"]+)" end_link="([^"]+)"')


def hhmmss(text):
    if not text:
        return None
    try:
        h, m, s = text.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except ValueError:
        return None


def read_selected_plans(path):
    """person -> (boundDriver list, [(mode, dep_s, from_link, to_link) ...]).

    Only the SELECTED plan, because that is the one the mobsim executes and the
    one the pairing engine reads.
    """
    people = {}
    pid = None
    bound = []
    in_selected = False
    legs = []
    pending_mode = None
    pending_dep = None
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        for line in fh:
            m = PERSON_RE.search(line)
            if m:
                if pid is not None:
                    people[pid] = (bound, legs)
                pid = m.group(1)
                bound, legs, in_selected = [], [], False
                continue
            if pid is None:
                continue
            a = ATTR_RE.search(line)
            if a and a.group(1) == 'boundDriver':
                bound = [x for x in a.group(2).split(',') if x]
                continue
            if SELECTED_RE.search(line):
                in_selected = True
                continue
            if in_selected and PLAN_END_RE.search(line):
                in_selected = False
                continue
            if not in_selected:
                continue
            lm = LEG_RE.search(line)
            if lm:
                pending_mode = lm.group(1)
                d = DEP_RE.search(line)
                pending_dep = hhmmss(d.group(1)) if d else None
                continue
            rm = ROUTE_RE.search(line)
            if rm and pending_mode is not None:
                legs.append((pending_mode, pending_dep,
                             rm.group(1), rm.group(2)))
                pending_mode = None
    if pid is not None:
        people[pid] = (bound, legs)
    return people


def classify(people, window_s, bound_window_s, capacity):
    """One verdict per declared ride leg."""
    car_legs = {}
    for pid, (_bound, legs) in people.items():
        cl = [l for l in legs if l[0] == 'car']
        if cl:
            car_legs[pid] = cl
    verdict = collections.Counter()
    gaps = []
    for pid, (bound, legs) in people.items():
        for mode, dep, frm, to in legs:
            if mode != 'ride':
                continue
            if not bound:
                verdict['no_declared_driver'] += 1
                continue
            best = None
            for drv in bound:
                for _m, ddep, dfrm, dto in car_legs.get(drv, ()):
                    both = (dfrm == frm and dto == to)
                    dest = (dto == to)
                    orig = (dfrm == frm)
                    gap = (abs((ddep or 0) - (dep or 0))
                           if dep is not None and ddep is not None else None)
                    rank = (0 if both else 1 if dest else 2 if orig else 3)
                    cand = (rank, gap if gap is not None else 10 ** 9)
                    if best is None or cand < best[0]:
                        best = (cand, both, dest, orig, gap)
            if best is None:
                verdict['driver_no_car_leg'] += 1
                continue
            (_rank, _g), both, dest, orig, gap = best
            if both:
                if gap is not None and gap <= bound_window_s:
                    verdict['paired_ok'] += 1
                else:
                    verdict['window_only'] += 1
                    if gap is not None:
                        gaps.append(gap / 60.0)
            elif dest:
                verdict['dest_only'] += 1
            elif orig:
                verdict['origin_only'] += 1
            else:
                verdict['neither_endpoint'] += 1
    return verdict, gaps


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--it', type=int, required=True)
    a = ap.parse_args()

    path = _os.path.join(a.run, 'output', 'ITERS', 'it.%d' % a.it,
                         '%d.plans.xml.gz' % a.it)
    if not _os.path.exists(path):
        raise SystemExit(
            'no selected-plans file at %s. Plans are written on '
            'controler.writePlansInterval, so not every iteration has one.'
            % path)

    found = windows_from_run(a.run)
    bound_s = float(found['boundWindowMinutes']) * 60.0
    capacity = int(float(found.get('maxPassengersPerVehicle', 4)))
    cfg = _registry.load(strict=True)
    # the inferred window is not emitted per run; it is the registry's, and it
    # has not moved since 9.81
    window_s = float(cfg.get('B.ride.pairing_window_min')) * 60.0

    print('reading %s ...' % path)
    people = read_selected_plans(path)
    verdict, gaps = classify(people, window_s, bound_s, capacity)

    total = sum(verdict.values())
    stamp = time.strftime('%Y-%m-%dT%H:%M:%S')
    print('=' * 78)
    print('DECLARED RIDE PAIRING   %s   run %s   iteration %d'
          % (stamp, _os.path.basename(_os.path.normpath(a.run)), a.it))
    print('basis  the SELECTED plans the pairing engine reads at BeforeMobsim')
    print('window %.0f min inferred / %.0f min for a declared pair '
          "(READ FROM THIS RUN'S OWN config.xml)"
          % (window_s / 60.0, bound_s / 60.0))
    print('=' * 78)
    print('%-22s %10s %8s' % ('verdict', 'ride legs', 'share'))
    for k in ('paired_ok', 'window_only', 'dest_only', 'origin_only',
              'neither_endpoint', 'driver_no_car_leg', 'no_declared_driver'):
        n = verdict.get(k, 0)
        print('%-22s %10d %7.2f%%'
              % (k, n, 100.0 * n / total if total else 0.0))
    print('%-22s %10d' % ('TOTAL ride legs', total))
    if gaps:
        gaps.sort()
        print('\nwindow_only gap minutes: median %.1f  p90 %.1f  min %.1f'
              % (gaps[len(gaps) // 2], gaps[int(0.9 * len(gaps)) - 1], gaps[0]))
    print('\nRead dest_only against neither_endpoint: the first is a RULE '
          'question\n(the driver reaches the destination, which is what a '
          'drop-off is), the second\nis a COHERENCE question (the driver is '
          'making a different trip entirely).')


if __name__ == '__main__':
    main()
