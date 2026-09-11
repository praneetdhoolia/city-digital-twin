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
import csv
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, 'src'))

RAW = os.path.join(REPO, 'results', 'raw')




def stall_kill_s():
    """The registry's own stall rule, RUN.gate.stall_kill_s - an iteration
    longer than the silence that kills a run IS a stall by that definition,
    and the pricer excludes it from the pace and the setup it carries. Read
    from the registry so the pricer and the killer cannot disagree."""
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), 'registry'))
        import registry as _registry                          # noqa: PLC0415
        return float(_registry.load().get('RUN.gate.stall_kill_s'))
    except Exception:                                          # noqa: BLE001
        return None


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _launch_stamp(name: str) -> str:
    return name[len('aborted_'):] if name.startswith('aborted_') else name


def _hms(v):
    """Seconds from a stopwatch HH:MM:SS cell, or None when it did not fire."""
    if not v or ':' not in v:
        return None
    try:
        h, m, s = v.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except ValueError:
        return None


def plain_iteration_pace(run_dir):
    """The pace of an iteration a 300-iteration arm actually REPEATS.

    A run's `median_iteration_s` is a median over every iteration it ran, and
    on a short probe most of those iterations are not the iteration an arm
    pays 300 times:

      * iteration 0 warms the JIT and writes the first plan dump;
      * `dump all plans` fires at iterations 0 and 1 ONLY - 59 s and 61 s of a
        213 s iteration on 20260908T014214_4it_25pct - and never again;
      * the LAST iteration writes the run's final output (350 s against 213 s
        on the same probe).

    On a 4-iteration probe that is three of five iterations, and the median
    lands 31% above the recurring cost: 282.6 s quoted against 213 and 219 s
    measured. This is trap 4 of the brief - "a median over a phase that fires
    in some iterations is not a cost" - which 9.155 taught `compare_runs.py`
    to flag and left in the pricer, where it prices approvals.

    Returns None when the stopwatch is unreadable, else the plain median, how
    many iterations it rests on, the one-off iterations by name, and the
    highest iteration index the run reached (a run that never reached a
    milestone iteration cannot have priced one).
    """
    path = os.path.join(run_dir, 'output', 'stopwatch.csv')
    if not os.path.exists(path):
        return None
    try:
        with io.open(path, encoding='utf-8') as fh:
            rows = list(csv.reader(fh, delimiter=';'))
    except (OSError, csv.Error):
        return None
    if len(rows) < 2:
        return None
    head = rows[0]
    # The header repeats its phase names - the first block holds clock STAMPS
    # and the second holds DURATIONS - so every lookup takes the LAST match.
    def last_index(name):
        for i in range(len(head) - 1, -1, -1):
            if head[i] == name:
                return i
        return None
    i_total = last_index('iteration')
    i_dump = last_index('dump all plans')
    if i_total is None or i_total == 0:
        return None
    seen = {}
    for r in rows[1:]:
        if not r or not r[0].strip().isdigit() or len(r) <= i_total:
            continue
        total = _hms(r[i_total])
        if total is None:
            continue
        dump = _hms(r[i_dump]) if i_dump is not None and len(r) > i_dump else None
        seen[int(r[0])] = (total, dump or 0)
    if not seen:
        return None
    last_it = max(seen)
    one_off, plain = {}, {}
    for it, (total, dump) in seen.items():
        if it == 0:
            one_off[it] = total          # JIT warm-up and the first dump
        elif dump > 0:
            one_off[it] = total          # `dump all plans` fires here and nowhere else
        elif it == last_it and len(seen) > 1:
            one_off[it] = total          # the final output write
        else:
            plain[it] = total
    if not plain:
        return None
    vals = sorted(plain.values())
    median = (vals[len(vals) // 2] if len(vals) % 2
              else 0.5 * (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]))
    return dict(plain_median_s=float(median), n_plain=len(plain),
                plain_iterations=sorted(plain), one_off_s=dict(one_off),
                last_iteration=last_it)


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
        # From the run's OWN per-iteration clock where the digest recorded
        # one: `wall - median x n` booked F33 arm 0's 13.1 h stall inside
        # iteration 89 as "13.9 h of setup" and quoted the next arm at 34.9 h
        # against a measured 6 min of setup (12 September 2026). A stall is
        # neither pace nor setup; it is named here and priced as neither.
        recorded = prog.get('iteration_seconds') or {}
        stalls = {}
        if recorded:
            secs = {int(k): float(v) for k, v in recorded.items()}
            limit = stall_kill_s()
            if limit:
                stalls = {k: v for k, v in secs.items() if v > limit}
            if wall:
                setup = max(0.0, float(wall) - sum(secs.values()))
        elif wall and reached:
            spent = float(median) * (int(reached) + 1)
            setup = max(0.0, float(wall) - spent)
        out.append(dict(
            name=name,
            # What an iteration costs when it pays only what every iteration
            # pays - read from the run's own stopwatch, not from its median.
            plain=plain_iteration_pace(d),
            # A run that carried a flight recorder paid for it: the first two
            # profiled probes ran ~8 % slower than the same stack unprofiled.
            # Its clock prices its own conditions and nothing else, so it is
            # kept - the reader may want it - and skipped when pricing.
            profiled=os.path.exists(os.path.join(d, 'profile.jfr')),
            fraction=fraction,
            median_iteration_s=float(median),
            reached_iteration=int(reached),
            setup_s=setup,
            # iterations that were a stall, not a pace (seconds each)
            stalls_s=stalls,
            completion=rec.get('completion') or meta.get('status'),
            family=rec.get('family') or meta.get('family'),
            # The committed Java this run EXECUTED. Resume detection has
            # refused to match across a change in it since issue #28; the
            # pricer never looked, and so priced a stack that no longer
            # existed.
            controler_sha256=rec.get('controler_sha256')
            or meta.get('controler_sha256'),
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

    # Price the RECURRING iteration, and carry the one-offs once each. The
    # record's median is a median over every iteration the run ran, and on a
    # short probe that is dominated by iterations an arm pays once: on
    # 20260908T014214_4it_25pct it quoted 282.6 s against a measured 213 and
    # 219 s, because three of its five iterations were iteration 0, the second
    # `dump all plans` and the final output write.
    plain = newest.get('plain')
    priced_on_plain = False
    if plain and iterations > len(plain['one_off_s']):
        one_off_total = float(sum(plain['one_off_s'].values()))
        recurring = iterations - len(plain['one_off_s'])
        quote_s = setup_s + one_off_total + plain['plain_median_s'] * recurring
        priced_on_plain = True

    # A probe that never reached a milestone iteration cannot have priced one.
    # The honest top of the band is the newest LONG arm's all-in median, which
    # paid every milestone it met.
    long_arm = next((a for a in same if a['reached_iteration'] >= 50), None)
    long_quote_s = (long_arm['median_iteration_s'] * iterations + setup_s
                    if long_arm else None)
    milestone_warning = None
    if priced_on_plain and plain['last_iteration'] < 10:
        milestone_warning = (
            'THE PRICED RUN REACHED ITERATION %d, so no milestone iteration is '
            'in this quote. A long arm writes milestone output periodically and '
            'pays for it, and a 4-iteration probe never meets one.%s'
            % (plain['last_iteration'],
               (' The newest arm at this fraction that ran past 50 - %s - held '
                '%.1f s an iteration all-in, which prices the same %d '
                'iterations at %s. Treat that as the TOP of the band and this '
                'quote as the bottom.'
                % (long_arm['name'], long_arm['median_iteration_s'], iterations,
                   _fmt_hours(long_quote_s))) if long_arm else ''))

    # The exclusion above is right - the recorder is ~8% of a profiled run's
    # clock - but it is SILENT, and silence is how it quoted a stale price
    # (9.155). After 9.154 the only runs carrying the repaired stack were
    # profiled probes, so every one was excluded and the quote fell back to a
    # pre-repair arm at 376.4 s: 26.3 h against a measured 13.5-18 h, asking
    # the operator to approve 8-12 hours the model no longer needs. A price
    # that rests on a run OLDER than runs it threw away must say so.
    stale_warning = None
    excluded = [a for a in arms
                if (fraction is None or a['fraction'] == fraction)
                and a.get('profiled')]
    # by LAUNCH STAMP, not by raw name: an `aborted_` prefix sorts after every
    # digit, so a string compare silently hid three of the four newer probes.
    newest_stamp = _launch_stamp(str(newest.get('name', '')))
    newer_excluded = [a for a in excluded
                      if _launch_stamp(str(a.get('name', ''))) > newest_stamp]
    if newer_excluded:
        fastest = min(a['median_iteration_s'] for a in newer_excluded)
        stale_warning = (
            'PRICED ON A RUN THAT IS NOT THE NEWEST. %d profiled run(s) at '
            'this fraction are NEWER than %s and were excluded because the '
            'flight recorder is in their clock (~8%%). The FASTEST of them '
            'measured %.1f s an iteration against the %.1f s quoted here, so '
            'this quote may be high by roughly %.0f%%. Take one UNPROFILED '
            'probe before spending an approval on it.'
            % (len(newer_excluded), newest.get('name'), fastest,
               newest['median_iteration_s'],
               100.0 * (1.0 - fastest / newest['median_iteration_s'])
               if newest['median_iteration_s'] else 0.0))
    # A STALE BUILD, which is a different thing from a stale RUN and was
    # invisible here. The quote above rests on what a JVM did; if the JVM that
    # will run the arm is built from different sources, the quote prices
    # something else. 9.153: the F30 arm ran 45 % over a price read from a
    # stack differing by ONE LINE.
    build_warning = None
    try:
        import sys as _sys
        _here = os.path.dirname(os.path.abspath(__file__))
        _run = os.path.join(os.path.dirname(_here), 'run')
        if _run not in _sys.path:
            _sys.path.insert(0, _run)
        import run_matsim as _rm
        current = _rm.controler_sha256()
    except Exception:                                          # noqa: BLE001
        current = None
    priced_build = (newest or {}).get('controler_sha256')
    if current and priced_build and current != priced_build:
        build_warning = (
            'PRICED ON A DIFFERENT BUILD. %s executed controler %s; the arm '
            'this quote is for would execute %s. The committed Java has '
            'changed since the priced run, so this is a price for a stack that '
            'no longer exists - and a new scoring term or event handler lands '
            'inside the mobsim, which is three quarters of an iteration. Take '
            'ONE short unprofiled probe at this fraction on the current build '
            'before spending an approval on this number (9.153: an arm once '
            'ran 45%% over a price read from a stack differing by one line).'
            % (newest.get('name'), priced_build[:16], current[:16]))
    elif current and not priced_build:
        build_warning = (
            'THE PRICED RUN DOES NOT RECORD ITS BUILD. %s carries no '
            'controler_sha256, so whether it executed the Java this arm would '
            'execute cannot be told from its record. Treat the quote as a '
            'lower bound.' % (newest or {}).get('name'))

    stall_warning = None
    if newest.get('stalls_s'):
        stall_warning = (
            'THE PRICED RUN STALLED: iteration(s) %s took %s in all, excluded '
            'from the pace and from the setup carried here. Whatever stalled '
            'it (a heap at its ceiling, #66) is a risk the quote does not '
            'price.' % (', '.join(str(k) for k in sorted(newest['stalls_s'])),
                        _fmt_hours(sum(newest['stalls_s'].values()))))

    return dict(
        stall_warning=stall_warning,
        setup_s=setup_s,
        iterations=iterations,
        fraction=fraction,
        priced_on=newest,
        excluded_newer_profiled=[a.get('name') for a in newer_excluded],
        stale_warning=stale_warning,
        milestone_warning=milestone_warning,
        build_warning=build_warning,
        priced_on_plain=priced_on_plain,
        plain=plain,
        long_arm=long_arm,
        long_quote_s=long_quote_s,
        quote_s=quote_s,
        quote=_fmt_hours(quote_s),
        low_s=medians[0] * iterations + setup_s,
        high_s=medians[-1] * iterations + setup_s,
        band=[_fmt_hours(medians[0] * iterations + setup_s),
              _fmt_hours(medians[-1] * iterations + setup_s)],
        recent=recent,
        gate_every=gate_every,
        first_gate_s=(((plain['plain_median_s'] if priced_on_plain
                        else newest['median_iteration_s']) * gate_every
                       + setup_s) if gate_every else None),
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
    pl = quote.get('plain')
    if quote.get('priced_on_plain'):
        print('  quote          %s   (%d recurring iterations x %.1f s, the '
              'one-off iterations at their own cost,' 
              % (quote['quote'],
                 quote['iterations'] - len(pl['one_off_s']),
                 pl['plain_median_s']))
        print('                 plus %s of setup before iteration 0)'
              % _fmt_hours(quote['setup_s']))
    else:
        print('  quote          %s   (%d iterations x %.1f s, plus %s of setup '
              'before iteration 0)'
              % (quote['quote'], quote['iterations'], on['median_iteration_s'],
                 _fmt_hours(quote['setup_s'])))
    print('  priced on      %s' % on['name'])
    if quote.get('priced_on_plain'):
        print('                 %.1f s on the %d iteration(s) that pay only '
              'what every iteration pays (%s), %s'
              % (pl['plain_median_s'], pl['n_plain'],
                 ', '.join(str(i) for i in pl['plain_iterations']),
                 on['completion'] or 'status unrecorded'))
        print('                 one-off: %s'
              % '; '.join('iteration %s %s s' % (k, v)
                          for k, v in sorted(pl['one_off_s'].items(),
                                             key=lambda kv: int(kv[0]))))
        print('                 (its own record says median %.1f s over every '
              'iteration - that median is NOT the recurring cost)'
              % on['median_iteration_s'])
    else:
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
    for key in ('build_warning', 'stale_warning', 'milestone_warning'):
        if quote.get(key):
            print()
            for i, sentence in enumerate(quote[key].split('. ')):
                if sentence:
                    print('  %s %s' % ('**' if i == 0 else '  ',
                                       sentence.rstrip('.') + '.'))
    print()
    print('  A STATED COST IS A BOUNDARY, NOT AN ESTIMATE. The spread above is')
    print('  what the same stack has actually done; the quote is the newest')
    print('  arm alone. Quote the RANGE to the user, and stop the arm at the')
    print('  cost that was approved rather than at the one it turned out to')
    print('  have. Nothing here is a result.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
