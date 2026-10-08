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

import city                                                       # noqa: E402

REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

RAW = os.path.join(REPO, 'results', 'raw')


def _arm_horizon_floor():
    """The iteration count from which a run is an ARM and not a probe: the
    floor of RUN.controler.last_iteration's declared sweep, the same line
    run.py's foreground refusal draws. Read from the registry; a registry
    that cannot be read makes nothing an arm."""
    try:
        import registry as _registry                          # noqa: PLC0415
        fields, _ = _registry.load_registry()
        lo = _registry._sweep_interval(
            fields['RUN.controler.last_iteration'].get('sweep'))
        return int(lo[0]) if lo else None
    except Exception:                                          # noqa: BLE001
        return None


def stall_kill_s():
    """The registry's own stall rule, RUN.gate.stall_kill_s - an iteration
    longer than the silence that kills a run IS a stall by that definition,
    and the pricer excludes it from the pace and the setup it carries. Read
    from the registry so the pricer and the killer cannot disagree."""
    try:
        import sys as _sys
        import registry as _registry                          # noqa: PLC0415
        return float(_registry.load().get('RUN.gate.stall_kill_s'))
    except Exception:                                          # noqa: BLE001
        return None


def probe_max_host_cpu_pct():
    """The registry's own bar on a probe's host, RUN.machine.probe_max_host_cpu_pct:
    a probe whose host read busier than this over its iterations priced the
    host, not the build, and is not quoted from. Read from the registry so
    the pricer and the declaration cannot disagree; None when unreadable."""
    try:
        import registry as _registry                          # noqa: PLC0415
        return float(_registry.load().get('RUN.machine.probe_max_host_cpu_pct'))
    except Exception:                                          # noqa: BLE001
        return None


def other_process_max_cores():
    """The launcher's bar on a co-tenant, RUN.machine.other_process_max_cores,
    read for the pricer's fallback on a host history written before
    `other_cpu_pct` existed; None when unreadable or declared off (0)."""
    try:
        import registry as _registry                          # noqa: PLC0415
        v = float(_registry.load().get('RUN.machine.other_process_max_cores'))
        return v or None
    except Exception:                                          # noqa: BLE001
        return None


def host_summary(run_dir):
    """What `_host.jsonl` says the host did while the run iterated, or None.

    The digest kept one sample - the last - until the sixteenth report, so
    the three daytime probes of 30 September 2026 quoted 37.0, 50.5 and
    27.7 h for one build with nothing in the pricer able to say which of
    them shared its host. The history is read through the digest's own
    reader; the summary is the busiest and the median host CPU over the
    samples taken inside an iteration, and the other process that held most
    cores at any sample.
    """
    try:
        import progress_digest                                 # noqa: PLC0415
        rows = progress_digest.read_host_history(run_dir)
    except Exception:                                          # noqa: BLE001
        return None
    cpu = sorted(r['cpu_pct'] for r in rows
                 if r.get('iteration') is not None and r.get('cpu_pct') is not None)
    other = sorted(r['other_cpu_pct'] for r in rows
                   if r.get('iteration') is not None and r.get('other_cpu_pct') is not None)
    if not cpu:
        return None
    top = None
    for r in rows:
        if r.get('iteration') is None:
            continue                      # the setup's co-tenants do not price an iteration
        p = r.get('top_other_process') or {}
        if p.get('cores') is not None and (top is None or p['cores'] > top['cores']):
            top = dict(p, iteration=r.get('iteration'), at=r.get('at'))
    return dict(samples=len(cpu), cpu_pct_max=cpu[-1],
                cpu_pct_median=cpu[len(cpu) // 2],
                other_cpu_pct_max=other[-1] if other else None,
                other_cpu_pct_median=other[len(other) // 2] if other else None,
                top_other_process=top)


def family_control(arms):
    """The newest family's control - its first run that ran to its last
    iteration at an arm's horizon - and the family's key, or (None, None).

    The 9.219 lesson: a probe launched in the day priced the host, and the
    one number that priced the build was the control's own wall clock. When
    a control exists in the family being priced, that wall is the pair
    quote and the probe's figure is the band around it.
    """
    try:
        import iteration_reading                              # noqa: PLC0415
        from build_run_index import load_families            # noqa: PLC0415
        fams, _ = load_families()
    except Exception:                                          # noqa: BLE001
        return None, None
    mine = [(k, f) for k, f in fams
            if (f.get('city') or city.DEFAULT_CITY) == city.CITY]
    if not mine:
        return None, None
    newest = mine[-1][0]
    floor = _arm_horizon_floor()
    if floor is None:
        return None, newest
    controls = []
    for a in arms:
        if a.get('completion') != 'ran_to_last_iteration' or not a.get('wall_s'):
            continue
        if a.get('reached_iteration', 0) < floor:
            continue
        try:
            fam, _, _ = iteration_reading.run_family(a['name'])
        except Exception:                                      # noqa: BLE001
            continue
        if fam == newest:
            controls.append(a)
    if not controls:
        return None, newest
    return min(controls, key=lambda a: _launch_stamp(a['name'])), newest


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
    i_begin = head.index('BEGIN iteration') if 'BEGIN iteration' in head else None
    begin0 = None
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
        if int(r[0]) == 0 and i_begin is not None and len(r) > i_begin:
            begin0 = _hms(r[i_begin])
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
                last_iteration=last_it,
                # every iteration the run's OWN clock timed, one-off or plain:
                # what the wall clock spent inside iterations
                iteration_total_s=float(sum(t for t, _ in seen.values())),
                # the wall-clock stamp (seconds past midnight) iteration 0
                # began at: launch to here is the run's setup, whatever
                # happened to the host afterwards
                first_iteration_begin_clock_s=begin0)


def launch_to_first_iteration_s(started, plain):
    """Seconds from the card's `started` to the stopwatch's BEGIN of iteration 0.

    This IS the setup - reading the network and plans and PersonPrepareForSim -
    and nothing after it. The other clocks subtract iterations from the wall,
    and the wall of a run whose host died holds the dead time: F36's arm 0
    priced the next arm at 62.9 h, 37.8 h of it "setup", against a real setup
    of 1,598 s (fourteenth report). Both stamps are local wall clock; setup
    is under a day, so the difference is taken modulo one.
    """
    begin = (plain or {}).get('first_iteration_begin_clock_s')
    if begin is None or not started:
        return None
    try:
        t = started.split('T', 1)[1]
        h, m, sec = (int(float(x)) for x in t.split(':')[:3])
    except (IndexError, ValueError):
        return None
    return float((begin - (h * 3600 + m * 60 + sec)) % 86400)


def setup_seconds(wall, reached, median, recorded, plain):
    """What a run spent OUTSIDE its iterations, from the clock that covers them.

    Three clocks can say it, in trust order:

    1. the harness's memo `_progress.json` `iteration_seconds` - but ONLY when
       it holds every iteration the run reached. The routers pair's harness
       died at iteration 34 while its JVM ran to 250 (DECISIONS.md 9.176), so
       its memo held 34 iterations and `wall - sum(memo)` booked the other
       216 as "22.8 h of setup", quoting the next arm at 48.8 h against a
       27.4 h run (16 September 2026);
    2. MATSim's own `output/stopwatch.csv`, which the JVM writes whether or
       not anything watches it, when it reaches the same last iteration;
    3. the record's median times the iterations, the estimate the memo replaced.

    `recorded` is {iteration: seconds} from the memo, `plain` is
    `plain_iteration_pace()`'s reading or None. Returns None when no clock
    can say.
    """
    if not wall:
        return None
    if reached is None:
        return None
    if recorded and max(recorded) >= int(reached):
        return max(0.0, float(wall) - sum(recorded.values()))
    if plain and plain.get('last_iteration', -1) >= int(reached)             and plain.get('iteration_total_s'):
        return max(0.0, float(wall) - float(plain['iteration_total_s']))
    if median:
        return max(0.0, float(wall) - float(median) * (int(reached) + 1))
    return None


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
        secs = {int(k): float(v) for k, v in recorded.items()}
        if secs:
            limit = stall_kill_s()
            if limit:
                stalls = {k: v for k, v in secs.items() if v > limit}
        # What an iteration costs when it pays only what every iteration
        # pays - read from the run's own stopwatch, not from its median.
        plain = plain_iteration_pace(d)
        # The memo covers only the iterations the harness lived to see; an
        # orphan's setup is read from the JVM's own stopwatch instead.
        setup = launch_to_first_iteration_s(meta.get('started'), plain)
        if setup is None:
            setup = setup_seconds(wall, reached, median, secs, plain)
        out.append(dict(
            name=name,
            city=meta.get('city') or city.DEFAULT_CITY,
            plain=plain,
            wall_s=wall,
            # the host across the run's iterations, from its own history
            # (None for a run that kept only the digest's last sample)
            host=host_summary(d),
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


def _outside_text(host):
    """The figure a refusal quotes: the CPU outside the run where the history
    carries it, else the busiest co-tenant and the cores it held."""
    if host.get('other_cpu_pct_max') is not None:
        return '%.0f %%' % float(host['other_cpu_pct_max'])
    top = host.get('top_other_process') or {}
    if top.get('cores') is not None:
        return '%s at %.2f cores' % (top.get('name', '?'), float(top['cores']))
    return 'an unrecorded amount'


def loaded_host(arm, max_cpu_pct, max_other_cores=None):
    """Whether this run's own host history says its clock priced the host:
    the busiest digest interval over its iterations read above the declared
    RUN.machine.probe_max_host_cpu_pct on the CPU OUTSIDE the run. The
    whole-host figure includes the run's own JVM - a 16-thread mobsim on 24
    cores reads 70-90 % by itself, and the first probe priced under this rule
    was refused at 98 % for its own work (9.221) - so the judgement is on
    `other_cpu_pct`; a history written before that field existed is judged
    on the busiest co-tenant's cores against RUN.machine.other_process_max_cores
    when that bar is given. A run with no history cannot say, and is not
    refused on what it cannot say."""
    host = arm.get('host') or {}
    if max_cpu_pct is None:
        return False
    if host.get('other_cpu_pct_max') is not None:
        return float(host['other_cpu_pct_max']) > float(max_cpu_pct)
    top = host.get('top_other_process') or {}
    if max_other_cores and top.get('cores') is not None:
        return float(top['cores']) > float(max_other_cores)
    return False


def price(iterations: int, fraction, arms: list, gate_every=None,
          first_iteration=None, max_host_cpu_pct=None, control=None,
          max_other_cores=None) -> dict:
    """The quote, and everything it rests on.

    `iterations` is the horizon, RUN.controler.last_iteration. A warm start
    (an overlay or `--warm-start` setting first_iteration N) runs only
    last - N of them from its checkpoint: F38's 175-iteration resume was
    quoted 32.4 h, the price of the whole 250 (fifteenth report). The pricer
    does not tell the post-cutoff tail's pace from the search's - one median
    prices both - so a resume is priced at the same per-iteration pace.

    A probe whose own `_host.jsonl` read busier than `max_host_cpu_pct`
    over its iterations is REFUSED as a price (the 9.219 lesson: a daytime
    probe prices the host, not the build), and when the family has a
    `control` that ran to its horizon, its wall clock is carried as the pair
    quote beside the probe's.
    """
    try:
        first_iteration = max(0, int(first_iteration or 0))
    except (TypeError, ValueError):
        first_iteration = 0
    horizon = int(iterations)
    iterations = max(0, horizon - first_iteration)
    # the same city's runs only: the store holds every city's (9.204)
    same = [a for a in arms
            if (fraction is None or a['fraction'] == fraction)
            and a.get('city', city.DEFAULT_CITY) == city.CITY
            and not a.get('profiled')]
    if max_other_cores is None and max_host_cpu_pct is not None:
        max_other_cores = other_process_max_cores()
    loaded = [a for a in same if loaded_host(a, max_host_cpu_pct, max_other_cores)]
    same = [a for a in same if a not in loaded]
    host_warning = None
    if loaded:
        host_warning = (
            'REFUSED AS A PRICE: %s - the host read %s busy OUTSIDE the run over the '
            'iterations of %s (RUN.machine.probe_max_host_cpu_pct %g), so the '
            'clock priced the host, not the build (9.219: the daytime probes '
            'of 30 September 2026 quoted 37.0-50.5 h for a 27.9 h build). '
            'Take the probe again on an idle host.'
            % (', '.join(a['name'] for a in loaded),
               ', '.join(_outside_text(a['host'] or {})
                         for a in loaded),
               'it' if len(loaded) == 1 else 'them', float(max_host_cpu_pct)))
    pair_quote = None
    if control and control.get('wall_s'):
        pair_quote = dict(name=control['name'], wall_s=float(control['wall_s']),
                          wall=_fmt_hours(float(control['wall_s'])),
                          reached_iteration=control.get('reached_iteration'))
    if not same:
        return dict(error=(
            'no run on disk measured a pace at fraction %s, so there is '
            'nothing to price this arm on (a profiled probe does not count: '
            'the recorder is in its clock%s). Run a short timing probe first '
            '(an overlay with RUN.controler.last_iteration = 4 and '
            'RUN.machine.jfr_profile false) and price the arm on that.'
            % (fraction, ('; neither does a probe on a loaded host - %s'
                          % host_warning) if host_warning else '')),
            host_warning=host_warning, pair_quote=pair_quote)
    # The newest run that timed a RECURRING iteration: a run stopped after two
    # iterations timed only one-offs (warm-up, the plans dump, its own last
    # write), and pricing on its all-in median quoted F37's relaunch at 39.5 h
    # against the probe's 32.0 h (26 September 2026). Fall back to the newest
    # run only when none timed one.
    newest = next((a for a in same if a.get('plain')), same[0])
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
        host_warning=host_warning,
        refused_loaded_host=[a['name'] for a in loaded],
        # the control's own wall, the pair quote when the family has one
        pair_quote=pair_quote,
        setup_s=setup_s,
        iterations=iterations,
        first_iteration=first_iteration,
        last_iteration=horizon,
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
        # a resume meets its first gate at the next milestone past its start
        first_gate_iteration=((first_iteration // gate_every + 1) * gate_every
                              if gate_every else None),
        first_gate_s=(((plain['plain_median_s'] if priced_on_plain
                        else newest['median_iteration_s'])
                       * ((first_iteration // gate_every + 1) * gate_every
                          - first_iteration)
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
    ap.add_argument('--first-iteration', type=int, default=None,
                    help='price a warm start from this checkpoint iteration '
                         '(default: the overlay\'s RUN.controler.first_iteration)')
    ap.add_argument('--json', action='store_true', help='machine-readable')
    args = ap.parse_args(argv)

    iterations, fraction, gate_every = args.iterations, args.fraction, None
    first = args.first_iteration
    if args.run_config or iterations is None or fraction is None:
        try:
            from registry import load as _load
            cfg = _load(scenario=args.scenario, day=args.day,
                        run=args.run_config)
            if iterations is None:
                iterations = cfg.get('RUN.controler.last_iteration')
            if fraction is None:
                fraction = cfg.get('RUN.sample.fraction')
            if first is None:
                # a resume overlay declares its checkpoint here
                first = cfg.get('RUN.controler.first_iteration')
            gate_every = cfg.get('RUN.gate.interval_iterations')
        except Exception as e:                                # noqa: BLE001
            if iterations is None or fraction is None:
                raise SystemExit(
                    'could not resolve the horizon and fraction from the '
                    'registry (%s).\nGive them directly: --iterations N '
                    '--fraction F' % e)

    arms = observed_arms()
    control, _ = family_control(arms)
    quote = price(int(iterations), fraction, arms, gate_every,
                  first_iteration=first or 0,
                  max_host_cpu_pct=probe_max_host_cpu_pct(), control=control)

    if args.json:
        print(json.dumps(quote, indent=2, sort_keys=True))
        return 1 if quote.get('error') else 0

    if quote.get('error'):
        print('CANNOT PRICE THIS ARM\n\n%s' % quote['error'])
        if quote.get('pair_quote'):
            print('\n  the family\'s control %s ran %s to iteration %s: the '
                  'pair quote' % (quote['pair_quote']['name'],
                                  quote['pair_quote']['wall'],
                                  quote['pair_quote']['reached_iteration']))
        return 1

    on = quote['priced_on']
    print('=' * 72)
    print('WHAT THIS ARM COSTS - %d iterations at %s of the population%s'
          % (quote['iterations'], ('%g%%' % (quote['fraction'] * 100))
             if quote['fraction'] else '?',
             (', resumed at iteration %d of %d' % (quote['first_iteration'],
                                                  quote['last_iteration']))
             if quote['first_iteration'] else ''))
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
    if quote.get('pair_quote'):
        # the 9.219 lesson: the control's own wall is the price of the build
        pq = quote['pair_quote']
        print('  pair quote     %s   (the family\'s control %s ran that to '
              'iteration %s; a treatment arm of the same build is priced by '
              'it, the probe above is the band)'
              % (pq['wall'], pq['name'], pq['reached_iteration']))
    if quote.get('first_gate_s'):
        print('  first gate     %s (iteration %d)'
              % (_fmt_hours(quote['first_gate_s']),
                 quote['first_gate_iteration']))
    print('  recent spread  %s to %s across the last %d arm(s) at this '
          'fraction' % (quote['band'][0], quote['band'][1],
                        len(quote['recent'])))
    print()
    print('  the arms this rests on, newest first')
    for a in quote['recent']:
        print('    %-44s %7.1f s/it  to it %-4d %s'
              % (a['name'], a['median_iteration_s'], a['reached_iteration'],
                 a['completion'] or ''))
    for key in ('build_warning', 'stale_warning', 'milestone_warning',
                'host_warning'):
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
