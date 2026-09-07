"""What the next arm will cost, priced on the newest arm's own stopwatch.

The rule this automates is written in two places and was broken anyway. The
brief says *"price the next arm on the newest arm's median and re-measure
before quoting a horizon"*; the record says *"a stated cost is a boundary, not
an estimate"*. Both were followed by hand, and by hand the F30 arm was priced
at 260 s an iteration from the arm before it and ran at 376 — 45 % over — while
the front-door README carried 45-50 hours, twice the board's figure, for nine
days. A number a human copies between documents is a number that rots.

So the price is READ, never typed:

  * every run directory that carries a record (`_run.json`) or a status card
    with a `median_iteration_s`, newest first;
  * the newest one at the same SAMPLE FRACTION as the arm being priced — a
    median from another fraction prices nothing, and this refuses to mix them;
  * the horizon from the overlay that would launch it, so the quote is of the
    arm actually proposed rather than of a round number.

It prints the quote, the run it came from, the spread across the recent arms
that bound it, and the gate milestones on the way - because a gate is a cost
boundary too, and the first question is usually not "how long is the arm" but
"when do I read it".

Nothing here launches, stops or reads a model output. It is arithmetic over
run records.

Usage
-----
    python src/analyse/arm_cost.py                       # the campaign default
    python src/analyse/arm_cost.py --run-config f29_gate_25pct
    python src/analyse/arm_cost.py --iterations 300 --fraction 0.25
    python src/analyse/arm_cost.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, 'src'))

RAW = os.path.join(REPO, 'results', 'raw')


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _launch_stamp(name: str) -> str:
    return name[len('aborted_'):] if name.startswith('aborted_') else name


def observed_arms(min_iterations: int = 2) -> list:
    """Every run that measured a per-iteration pace, newest launch first.

    A run counts when it carries a median and reached enough iterations for
    that median to mean anything. A STOPPED arm counts: its clock is citable
    even when its levels are not (9.148) - which is the whole reason a price
    can be read at all, since no arm since F4 has reached its horizon.
    """
    out = []
    if not os.path.isdir(RAW):
        return out
    for name in sorted(os.listdir(RAW), key=_launch_stamp, reverse=True):
        d = os.path.join(RAW, name)
        if not os.path.isdir(d):
            continue
        rec = _read(os.path.join(d, '_run.json')) or {}
        meta = _read(os.path.join(d, '_meta.json')) or {}
        prog = _read(os.path.join(d, '_progress.json')) or {}
        median = (rec.get('median_iteration_s')
                  or meta.get('median_iteration_s')
                  or (prog.get('pace') or {}).get('median_s'))
        if not median:
            continue
        reached = (rec.get('reached_iteration')
                   if rec.get('reached_iteration') is not None
                   else prog.get('iteration'))
        if reached is None or reached < min_iterations:
            continue
        fraction = (rec.get('fraction') or meta.get('fraction')
                    or prog.get('fraction'))
        # What the run spent OUTSIDE its iterations: reading the network and
        # the plans, and MATSim's own PersonPrepareForSim over every agent
        # before iteration 0. Measured at ~13 min on a 25 % run, which is
        # noise against a 300-iteration arm and half the cost of a 4-iteration
        # probe - so it is carried rather than folded into the median.
        wall = rec.get('wall_s') or meta.get('wall_s')
        setup = None
        if wall and reached:
            spent = float(median) * (int(reached) + 1)
            setup = max(0.0, float(wall) - spent)
        out.append(dict(
            name=name,
            # A run that carried a flight recorder paid for it: the first two
            # profiled probes ran ~8 % slower than the same stack unprofiled.
            # Its clock prices its own conditions and nothing else, so it is
            # kept - the reader may want it - and skipped when pricing.
            profiled=os.path.exists(os.path.join(d, 'profile.jfr')),
            fraction=fraction,
            median_iteration_s=float(median),
            reached_iteration=int(reached),
            setup_s=setup,
            completion=rec.get('completion') or meta.get('status'),
            family=rec.get('family') or meta.get('family'),
        ))
    return out


def _fmt_hours(seconds: float) -> str:
    h = seconds / 3600.0
    if h < 1:
        return '%d min' % round(seconds / 60.0)
    return '%.1f h' % h


def price(iterations: int, fraction, arms: list, gate_every=None) -> dict:
    """The quote, and everything it rests on."""
    same = [a for a in arms
            if (fraction is None or a['fraction'] == fraction)
            and not a.get('profiled')]
    if not same:
        return dict(error=(
            'no run on disk measured a pace at fraction %s, so there is '
            'nothing to price this arm on (a profiled probe does not count: '
            'the recorder is in its clock). Run a short timing probe first '
            '(an overlay with RUN.controler.last_iteration = 4 and '
            'RUN.machine.jfr_profile false) and price the arm on that.'
            % fraction))
    newest = same[0]
    recent = same[:5]
    medians = sorted(a['median_iteration_s'] for a in recent)
    setup_s = newest.get('setup_s') or 0.0
    quote_s = newest['median_iteration_s'] * iterations + setup_s
    return dict(
        setup_s=setup_s,
        iterations=iterations,
        fraction=fraction,
        priced_on=newest,
        quote_s=quote_s,
        quote=_fmt_hours(quote_s),
        low_s=medians[0] * iterations + setup_s,
        high_s=medians[-1] * iterations + setup_s,
        band=[_fmt_hours(medians[0] * iterations + setup_s),
              _fmt_hours(medians[-1] * iterations + setup_s)],
        recent=recent,
        gate_every=gate_every,
        first_gate_s=(newest['median_iteration_s'] * gate_every
                      if gate_every else None),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run-config', help='the run overlay that would launch it')
    ap.add_argument('--scenario', default=None)
    ap.add_argument('--day', default=None)
    ap.add_argument('--iterations', type=int,
                    help='override the horizon the overlay declares')
    ap.add_argument('--fraction', type=float,
                    help='override the sample fraction the overlay declares')
    ap.add_argument('--json', action='store_true', help='machine-readable')
    args = ap.parse_args(argv)

    iterations, fraction, gate_every = args.iterations, args.fraction, None
    if args.run_config or iterations is None or fraction is None:
        try:
            from registry import load as _load
            cfg = _load(scenario=args.scenario, day=args.day,
                        run=args.run_config)
            if iterations is None:
                iterations = cfg.get('RUN.controler.last_iteration')
            if fraction is None:
                fraction = cfg.get('RUN.sample.fraction')
            gate_every = cfg.get('RUN.gate.interval_iterations')
        except Exception as e:                                # noqa: BLE001
            if iterations is None or fraction is None:
                raise SystemExit(
                    'could not resolve the horizon and fraction from the '
                    'registry (%s).\nGive them directly: --iterations N '
                    '--fraction F' % e)

    arms = observed_arms()
    quote = price(int(iterations), fraction, arms, gate_every)

    if args.json:
        print(json.dumps(quote, indent=2, sort_keys=True))
        return 1 if quote.get('error') else 0

    if quote.get('error'):
        print('CANNOT PRICE THIS ARM\n\n%s' % quote['error'])
        return 1

    on = quote['priced_on']
    print('=' * 72)
    print('WHAT THIS ARM COSTS - %d iterations at %s of the population'
          % (quote['iterations'], ('%g%%' % (quote['fraction'] * 100))
             if quote['fraction'] else '?'))
    print('=' * 72)
    print('  quote          %s   (%d iterations x %.1f s, plus %s of setup '
          'before iteration 0)'
          % (quote['quote'], quote['iterations'], on['median_iteration_s'],
             _fmt_hours(quote['setup_s'])))
    print('  priced on      %s' % on['name'])
    print('                 median %.1f s an iteration over %d iteration(s), '
          '%s' % (on['median_iteration_s'], on['reached_iteration'],
                  on['completion'] or 'status unrecorded'))
    if on.get('family'):
        print('                 family %s' % on['family'])
    if quote.get('first_gate_s'):
        print('  first gate     %s (iteration %d)'
              % (_fmt_hours(quote['first_gate_s']), quote['gate_every']))
    print('  recent spread  %s to %s across the last %d arm(s) at this '
          'fraction' % (quote['band'][0], quote['band'][1],
                        len(quote['recent'])))
    print()
    print('  the arms this rests on, newest first')
    for a in quote['recent']:
        print('    %-44s %7.1f s/it  to it %-4d %s'
              % (a['name'], a['median_iteration_s'], a['reached_iteration'],
                 a['completion'] or ''))
    print()
    print('  A STATED COST IS A BOUNDARY, NOT AN ESTIMATE. The spread above is')
    print('  what the same stack has actually done; the quote is the newest')
    print('  arm alone. Quote the RANGE to the user, and stop the arm at the')
    print('  cost that was approved rather than at the one it turned out to')
    print('  have. Nothing here is a result.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
