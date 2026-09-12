#!/usr/bin/env python
"""Is a reading taken at one iteration stable enough to SCORE a candidate on?

Iteration 100 became this project's reading unit on COST - it is the gate the
runner watches (`RUN.gate.interval_iterations`) and roughly a fifth of an arm's
wall clock - and never on stability. Nothing had ever measured how much a mode's
own share still moves between one iteration and the next at that depth. That
matters before any parameter search is priced: a search compares two CANDIDATES
at a fixed reading point, and if a mode drifts further between iteration 80 and
100 of ONE run than two candidates would differ, the reading cannot resolve them
and the search is buying noise. The same question decides whether the search's
own stopping rule is meaningful: `CAL.search.convergence_delta` ends a
coordinate pass that improves the objective by less than a declared number of
percentage points, and a stopping rule smaller than the reading's natural drift
is a rule that fires on noise.

WHAT THIS COMPARES, AND WHAT IT REFUSES TO
------------------------------------------
**WITHIN ONE RUN ONLY.** Every figure here is one run's mode share at iteration
A against THE SAME RUN's mode share at iteration B. That is the only comparison
this script will make, and it is legitimate because both readings come from one
build, one seed, one set of inputs and one family - the same directory.

It NEVER differences two runs against each other, and neither may a reader of
its output. Arms in different comparability families (DECISIONS.md 3.5 and the
city's `docs/run_families.json`) are built on different inputs, and the model is
not bit-reproducible between builds in any case, so a difference between two
runs' shares is not a measurement of anything. Two runs appear in one report
here only so their SEPARATE drift figures can be read side by side, the way two
thermometers' precisions are compared without adding the temperatures.

WHAT IT MEASURES, PER RUN AND PER MODE
--------------------------------------
  * the modelled level at each of the two iterations, in that mode's own units
    (a share in per cent, or boardings per weekday for a mode whose target is
    on a boardings denominator);
  * `drift`, the later level minus the earlier one;
  * `deviation_drift_points`, the change in that mode's deviation from its own
    target, in points of per cent - the quantity the acceptance band
    (`CAL.gate.pass_deviation_pct`) is written in, so the two are directly
    comparable;
  * `drift_over_gap`, the drift as a fraction of the mode's remaining distance
    to its target: near 0 the reading is settled beside the error that is left,
    near or above 1 the reading moves as far as the error it is meant to
    measure;
  * the search's OWN objective at each iteration - `fit.py`'s mean absolute
    mode-share error in percentage points, scored through
    `measure_iteration_modes` so the survey folds cannot drift from the real
    fit - and its drift against `CAL.search.convergence_delta`.

Every threshold is declared in the registry and read from it; none is typed
here. The two iterations are the analyst's question and are given on the command
line.

    python src/analyse/measure_reading_stability.py --all --from 80
    python src/analyse/measure_reading_stability.py --run <name> --from 80 --to 100
    python src/analyse/measure_reading_stability.py --all --from 80 --json out.json

Reads run directories through the results store and the city's target artefact.
Writes nothing but the report and the file `--json` names. **Nothing here is a
result**: a run without `_run.json` is not a result no matter how it reads, and
a stopped arm's reading is citable at its record's `reached_iteration` and
nowhere past it.
"""

import os as _os
import sys as _sys

import io
import json
import argparse
import contextlib

import registry as _registry
import results_store as _store
import measure_iteration_modes as mim
import report_mode_ridership as rmr

# The acceptance band and the search's stopping delta are DECLARED values, not
# this script's opinion, so they are resolved like every other one.
_CFG = _registry.load(strict=True)
BAND_PCT = float(_CFG.get('CAL.gate.pass_deviation_pct'))
CONVERGENCE_DELTA = float(_CFG.get('CAL.search.convergence_delta'))
CONVERGENCE_DELTA_UNITS = _CFG.field('CAL.search.convergence_delta')['units']
GATE_INTERVAL = int(_CFG.get('RUN.gate.interval_iterations'))
# The windowed reading (9.159). A reading may be taken AT an iteration or
# AVERAGED over the declared window ending there; which one is under test is the
# analyst's question, so the default is the declared value and --window overrides
# it. 0 means the point reading this script was written to condemn.
READING_WINDOW = int(_CFG.get('CAL.gate.reading_window_iterations'))

# THE STOPPING DELTA IS COMPARED ONLY WITH A DRIFT IN ITS OWN UNITS. It has
# been declared both ways - percentage points of a folded mean, and relative
# per cent of the worst mode - and the two are not the same quantity. A share's
# drift is in percentage points; the change in a mode's deviation from its own
# target is in points of relative per cent. Dividing one by a delta stated in
# the other would be a units error dressed as a ratio, so each comparison is
# gated on the declared units rather than assumed.
DELTA_IN_PP = 'point' in CONVERGENCE_DELTA_UNITS.lower()
DELTA_IN_RELATIVE_PCT = not DELTA_IN_PP

# A mode whose target sits on a boardings denominator is measured in boardings
# a weekday, so its drift is not in percentage points and must not be pooled
# with the share modes' or compared against a stopping delta written in them.
PP_UNITS = 'percentage points'
LEVEL_UNITS = 'mode-specific (see denominator)'


def read_iteration(run_dir, iteration, window):
    """One reading of this run, and the search objective, silenced.

    `report_mode_ridership` is the gate reading a person would take; it leaves
    the numbers behind it in `LAST`. Nothing is re-implemented here - the same
    reader, at two depths. With `window` non-zero the reading is the mean over
    the readable tables inside that window ending at `iteration` (9.159), which
    is the same reader again: the window lives inside it precisely so this
    script cannot measure a different quantity from the one the gate uses.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if window:
            rmr.report_window(run_dir, iteration, window)
        else:
            rmr.report(run_dir, iteration)
    rows = {r['mode']: dict(r) for r in rmr.LAST['rows']}
    source = rmr.LAST['source']
    window_its = (rmr.LAST.get('window') or {}).get('iterations') or [iteration]
    # the folded objective over the same readings, so both statistics in this
    # report describe ONE reading rather than two different ones
    objs = []
    for _it in window_its:
        with contextlib.redirect_stdout(buf):
            _share, _scored, _out = mim.score(run_dir, _it)
        if (_scored or {}).get('mean_abs_pp') is not None:
            objs.append(_scored['mean_abs_pp'])
    scored = dict(mean_abs_pp=(round(sum(objs) / len(objs), 4) if objs
                               else None),
                  errors=(_scored or {}).get('errors', []))
    return dict(iteration=iteration, modes=rows, source=source,
                window_iterations=list(window_its),
                objective_mean_abs_pp=(scored or {}).get('mean_abs_pp'),
                objective_categories={e['hts_category']: e['modelled']
                                      for e in (scored or {}).get('errors', [])})


def _num(v):
    return v if isinstance(v, (int, float)) else None


def drift_table(early, late):
    """Per-mode drift between two readings OF ONE RUN."""
    out = []
    for mode in sorted(set(early['modes']) | set(late['modes'])):
        a, b = early['modes'].get(mode, {}), late['modes'].get(mode, {})
        m0, m1 = _num(a.get('modelled')), _num(b.get('modelled'))
        target = _num(b.get('target')) or _num(a.get('target'))
        d0, d1 = _num(a.get('deviation_pct')), _num(b.get('deviation_pct'))
        denominator = b.get('denominator') or a.get('denominator') or ''
        # a share is in per cent, so its drift is in percentage points; a
        # boardings target is not, and saying so is the point of the field
        share_like = not denominator.startswith('boardings per weekday')
        row = dict(mode=mode,
                   denominator=denominator,
                   basis=b.get('basis') or a.get('basis'),
                   units=PP_UNITS if share_like else denominator,
                   level_early=m0, level_late=m1, target=target,
                   deviation_pct_early=d0, deviation_pct_late=d1)
        row['drift'] = None if (m0 is None or m1 is None) else round(m1 - m0, 4)
        row['drift_pp'] = row['drift'] if share_like else None
        row['deviation_drift_points'] = (
            None if (d0 is None or d1 is None) else round(d1 - d0, 3))
        # the drift measured against the error the reading exists to detect
        gap = None if (m1 is None or target in (None, 0)) else abs(m1 - target)
        row['gap_to_target'] = None if gap is None else round(gap, 4)
        row['drift_over_gap'] = (
            None if (row['drift'] is None or not gap) else
            round(abs(row['drift']) / gap, 4))
        # and against the band the directive is written in
        row['deviation_drift_over_band'] = (
            None if row['deviation_drift_points'] is None else
            round(abs(row['deviation_drift_points']) / BAND_PCT, 4))
        # and, for a share mode only, against the search's stopping delta
        row['drift_over_convergence_delta'] = (
            None if (row['drift_pp'] is None or not DELTA_IN_PP) else
            round(abs(row['drift_pp']) / CONVERGENCE_DELTA, 3))
        row['deviation_drift_over_convergence_delta'] = (
            None if (row['deviation_drift_points'] is None
                     or not DELTA_IN_RELATIVE_PCT) else
            round(abs(row['deviation_drift_points']) / CONVERGENCE_DELTA, 3))
        out.append(row)
    return out


def measure(run_dir, it_early, it_late, window):
    """Both readings of ONE run and the drift between them."""
    early = read_iteration(run_dir, it_early, window)
    late = read_iteration(run_dir, it_late, window)
    rows = drift_table(early, late)
    obj0, obj1 = early['objective_mean_abs_pp'], late['objective_mean_abs_pp']
    obj_drift = None if (obj0 is None or obj1 is None) else round(obj1 - obj0, 4)
    scored = [r for r in rows if r['drift_pp'] is not None
              and r['deviation_drift_points'] is not None]
    worst_pp = max(scored, key=lambda r: abs(r['drift_pp']), default=None)
    worst_dev = max(scored, key=lambda r: abs(r['deviation_drift_points']),
                    default=None)
    return dict(
        run=_os.path.basename(_os.path.normpath(run_dir)),
        iteration_early=it_early, iteration_late=it_late,
        reading_window_iterations=window,
        window_early=early.get('window_iterations'),
        window_late=late.get('window_iterations'),
        windows_overlap=bool(set(early.get('window_iterations') or [])
                             & set(late.get('window_iterations') or [])),
        fraction=rmr.sample_fraction(run_dir),
        source=late['source'],
        modes=rows,
        objective_mean_abs_pp_early=obj0,
        objective_mean_abs_pp_late=obj1,
        objective_drift_pp=obj_drift,
        objective_drift_over_convergence_delta=(
            None if (obj_drift is None or not DELTA_IN_PP) else
            round(abs(obj_drift) / CONVERGENCE_DELTA, 3)),
        worst_share_drift_pp=(None if worst_pp is None else
                              dict(mode=worst_pp['mode'],
                                   drift_pp=worst_pp['drift_pp'])),
        worst_deviation_drift_points=(
            None if worst_dev is None else
            dict(mode=worst_dev['mode'],
                 points=worst_dev['deviation_drift_points'])),
    )


def _cell(value, width, places):
    """One table cell: a number at the given width, or a dash for absent."""
    if isinstance(value, (int, float)):
        return '%*.*f' % (width, places, value)
    return '%*s' % (width, '-')


def print_run(block):
    print('=' * 104)
    print('WITHIN-RUN DRIFT   run %s   iteration %d -> %d   fraction %s'
          % (block['run'], block['iteration_early'], block['iteration_late'],
             block['fraction']))
    if block.get('reading_window_iterations'):
        print('reading WINDOWED over %d iterations: %s  vs  %s%s'
              % (block['reading_window_iterations'],
                 ','.join('it.%d' % i for i in block['window_early'] or []),
                 ','.join('it.%d' % i for i in block['window_late'] or []),
                 '   *** THE TWO WINDOWS SHARE AN ITERATION, which damps the '
                 'drift by construction - read the non-overlapping pair beside '
                 'it' if block.get('windows_overlap') else
                 '   (no shared iteration)'))
    print('basis  %s; the SAME run at two depths - never differenced against '
          'another run' % block['source'])
    print('=' * 104)
    print('%-15s %12s %12s %12s %10s %11s %9s %9s'
          % ('mode', 'at %d' % block['iteration_early'],
             'at %d' % block['iteration_late'], 'drift', 'target',
             'dev pts', '/band', '/delta'))
    print('-' * 104)
    for r in block['modes']:
        print('%-15s %s %s %s %s %s %s %s'
              % (r['mode'],
                 _cell(r['level_early'], 12, 4),
                 _cell(r['level_late'], 12, 4),
                 _cell(r['drift'], 12, 4),
                 _cell(r['target'], 10, 2),
                 _cell(r['deviation_drift_points'], 11, 2),
                 _cell(r['deviation_drift_over_band'], 9, 3),
                 _cell(r['drift_over_convergence_delta']
                       if DELTA_IN_PP
                       else r['deviation_drift_over_convergence_delta'],
                       9, 2)))
    print('-' * 104)
    print('dev pts  = change in this mode\'s deviation from its own target, in '
          'points of per cent')
    print('/band    = that change over the declared acceptance band '
          '(CAL.gate.pass_deviation_pct = %g%%)' % BAND_PCT)
    print('/delta   = %s over the search\'s stopping delta '
          '(CAL.search.convergence_delta = %g %s)'
          % ('the drift, share modes only' if DELTA_IN_PP
             else 'the deviation change',
             CONVERGENCE_DELTA, CONVERGENCE_DELTA_UNITS))
    o0, o1, od = (block['objective_mean_abs_pp_early'],
                  block['objective_mean_abs_pp_late'],
                  block['objective_drift_pp'])
    if od is not None:
        print('SEARCH OBJECTIVE (fit.py mean abs mode-share error, pp): '
              '%.4f -> %.4f, drift %+.4f%s'
              % (o0, o1, od,
                 (' = %.2f x the %g pp stopping delta'
                  % (abs(od) / CONVERGENCE_DELTA, CONVERGENCE_DELTA))
                 if DELTA_IN_PP else
                 ' (the declared stopping delta is %g %s - a different '
                 'quantity, so the two are not divided)'
                 % (CONVERGENCE_DELTA, CONVERGENCE_DELTA_UNITS)))
    print()


def readable(run_dir, iteration):
    """Can this iteration be read at all - table or experienced plans?

    A run writes its per-iteration trips table on the interval its config
    declares, so an iteration can be perfectly readable and still have no
    table: `iteration_trips.py` derives the same linked trips from that
    iteration's experienced plans and is validated to reproduce the table
    exactly wherever both exist. Filtering on the table alone would have
    dropped four of the six arms that reached the reading point.
    """
    import iteration_trips as itr
    try:
        if iteration in set(mim.iterations_with_trips(run_dir)):
            return True
        return itr.plans_path(run_dir, iteration) is not None
    except OSError:
        return False


def runs_with(it_early, it_late):
    """Every run whose BULK still holds both iterations, in either form."""
    found = []
    for name in _store.run_names():
        bulk = _store.resolve(name)
        if bulk is None:
            continue
        if readable(bulk, it_early) and readable(bulk, it_late):
            found.append(bulk)
    return found


def verdict(blocks, it_early, it_late):
    """The answer the measurement supports, in the arithmetic's own terms.

    Every statement here is a count or an extremum over the per-run figures.
    Pooling those is NOT a cross-run comparison of mode shares - it is a
    distribution of each run's OWN precision, the way two instruments' error
    bars are compared without adding their readings.
    """
    if not blocks:
        return dict(measured_runs=0, answer='nothing was measured')
    objs = [b['objective_drift_pp'] for b in blocks
            if b['objective_drift_pp'] is not None]
    # The stopping delta is only comparable with a drift in its own units.
    # Where it is stated in percentage points the objective's own drift is the
    # comparison; where it is stated in relative per cent the comparable
    # quantity is each mode's deviation change, which is counted below.
    over_delta = [b['run'] for b in blocks
                  if DELTA_IN_PP and b['objective_drift_pp'] is not None
                  and abs(b['objective_drift_pp']) > CONVERGENCE_DELTA]
    over_delta_modes = []
    # a mode whose deviation moves by more than the whole acceptance band in
    # this window cannot be resolved at this reading point at all
    per_mode = {}
    for b in blocks:
        for r in b['modes']:
            d = r['deviation_drift_points']
            if d is None:
                continue
            cur = per_mode.setdefault(r['mode'],
                                      dict(mode=r['mode'], runs=0,
                                           runs_over_band=0,
                                           max_abs_points=0.0))
            cur['runs'] += 1
            cur['max_abs_points'] = max(cur['max_abs_points'], abs(d))
            if abs(d) > BAND_PCT:
                cur['runs_over_band'] += 1
            if DELTA_IN_RELATIVE_PCT and abs(d) > CONVERGENCE_DELTA:
                over_delta_modes.append(dict(run=b['run'], mode=r['mode'],
                                             points=d))
    over_band = sorted((m for m in per_mode.values() if m['runs_over_band']),
                       key=lambda m: -m['max_abs_points'])
    scorable = (it_late if not over_delta and not over_delta_modes
                and not over_band else None)
    return dict(
        measured_runs=len(blocks),
        window='iteration %d to %d, within each run' % (it_early, it_late),
        objective_drift_pp_range=[min(objs), max(objs)] if objs else None,
        objective_drift_all_same_sign=bool(
            objs and (all(o > 0 for o in objs) or all(o < 0 for o in objs))),
        stopping_delta=CONVERGENCE_DELTA,
        stopping_delta_units=CONVERGENCE_DELTA_UNITS,
        runs_whose_objective_drift_exceeds_the_stopping_delta=over_delta,
        readings_whose_deviation_drift_exceeds_the_stopping_delta=(
            over_delta_modes),
        modes_whose_deviation_drift_exceeds_the_band=over_band,
        iteration_is_scorable=scorable is not None,
        answer=(
            'iteration %d IS a scorable reading point on this evidence: '
            'nothing moved further than the %g %s stopping delta and no '
            'mode\'s deviation moved further than the %g%% acceptance band '
            'between iteration %d and %d of any run measured'
            % (it_late, CONVERGENCE_DELTA, CONVERGENCE_DELTA_UNITS, BAND_PCT,
               it_early, it_late)
            if scorable is not None else
            'iteration %d is NOT a scorable reading point: between iteration '
            '%d and %d of the SAME run, %s, and %d mode(s) moved further from '
            'or towards target than the whole %g%% acceptance band. A '
            'candidate scored here would be resolved by how far the run had '
            'got, not by its parameters.'
            % (it_late, it_early, it_late,
               ('the search objective itself moved more than the %g %s delta '
                'the search would stop on in %d of %d runs'
                % (CONVERGENCE_DELTA, CONVERGENCE_DELTA_UNITS,
                   len(over_delta), len(blocks)))
               if DELTA_IN_PP else
               ('%d per-mode reading(s) moved further than the %g %s delta '
                'the search would stop on'
                % (len(over_delta_modes), CONVERGENCE_DELTA,
                   CONVERGENCE_DELTA_UNITS)),
               len(over_band), BAND_PCT)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', action='append', default=[],
                    help='run name or directory; repeatable')
    ap.add_argument('--all', action='store_true',
                    help='every run in the store holding both iterations')
    ap.add_argument('--to', type=int, default=GATE_INTERVAL,
                    help='the later iteration - the reading point under test '
                         '(default: the gate interval, '
                         'RUN.gate.interval_iterations = %d)' % GATE_INTERVAL)
    # THE EARLIER ITERATION IS THE ANALYST'S QUESTION AND IS NOT GUESSED. How
    # far back "lately" reaches is what the measurement is asking, and a
    # default here would answer it silently in a script, which is the one thing
    # this repo does not allow a number to do.
    ap.add_argument('--from', dest='frm', type=int, required=True,
                    help='the earlier iteration the reading is compared with')
    # The DEFAULT IS THE DECLARED WINDOW, not a point. A default of 0 here
    # would put the reading this project measured to be unscorable back in the
    # instrument as its resting state, decided in a script rather than in the
    # registry. `--window 0` asks for the point reading explicitly.
    ap.add_argument('--window', type=int, default=READING_WINDOW, metavar='N',
                    help='average the reading over the readable iterations in '
                         'the last N (CAL.gate.reading_window_iterations = %d) '
                         'instead of taking it at a point; 0 is the point '
                         'reading (9.159). Default: the declared '
                         'CAL.gate.reading_window_iterations' % READING_WINDOW)
    ap.add_argument('--json', help='write the whole measurement to this path')
    a = ap.parse_args()

    it_late = a.to
    it_early = a.frm
    if it_early >= it_late:
        raise SystemExit('the earlier iteration (%d) must precede the later '
                         '(%d)' % (it_early, it_late))

    dirs = []
    for name in a.run:
        bulk = _store.resolve(name)
        if bulk is None:
            raise SystemExit(
                'no BULK for %s - the results store keeps a run\'s findings in '
                'processed forever but its per-iteration tables only while the '
                'raw cache holds them' % name)
        dirs.append(bulk)
    if a.all:
        for bulk in runs_with(it_early, it_late):
            if bulk not in dirs:
                dirs.append(bulk)
    if not dirs:
        raise SystemExit('no run to measure: give --run, or --all (no run in '
                         'the store holds both iteration %d and %d)'
                         % (it_early, it_late))

    blocks = []
    for bulk in dirs:
        needed = [it_early, it_late]
        if a.window:
            needed = sorted(set(
                rmr.window_iterations(bulk, it_early, a.window)
                + rmr.window_iterations(bulk, it_late, a.window)) or needed)
        missing = [i for i in needed if not readable(bulk, i)]
        if missing:
            print('skipping %s: nothing readable at iteration %s'
                  % (_os.path.basename(_os.path.normpath(bulk)),
                     ', '.join(str(i) for i in missing)), flush=True)
            continue
        block = measure(bulk, it_early, it_late, a.window)
        print_run(block)
        blocks.append(block)

    doc = dict(question='is a%s reading at iteration %d stable enough to '
                        'score a candidate on?'
                        % (' %d-iteration WINDOWED' % a.window if a.window
                           else ' POINT', it_late),
               reading_window_iterations=a.window,
               verdict=verdict(blocks, it_early, it_late),
               comparison='WITHIN-RUN ONLY: one run at iteration %d against '
                          'the same run at iteration %d. No two runs are '
                          'differenced against each other, and a reader must '
                          'not do so either - these arms sit in different '
                          'comparability families.' % (it_early, it_late),
               iteration_early=it_early, iteration_late=it_late,
               acceptance_band_pct=BAND_PCT,
               convergence_delta=CONVERGENCE_DELTA,
               convergence_delta_units=CONVERGENCE_DELTA_UNITS,
               gate_interval_iterations=GATE_INTERVAL,
               runs=blocks)
    print('=' * 104)
    print('VERDICT  %s' % doc['verdict']['answer'])
    print('=' * 104)
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(doc, fh, indent=1)
        print('wrote %s' % a.json)
    return 0


if __name__ == '__main__':
    _sys.exit(main())
