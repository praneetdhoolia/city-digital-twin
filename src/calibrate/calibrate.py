#!/usr/bin/env python
"""P4 deliverable 4: the calibration loop.

Deterministic, resumable, and structurally unable to read a holdout row.

**It cannot see the holdout.** This module never opens the validation targets. It
calls `run_matsim` and `extract_metrics`, then `fit`, and reads the `_fit.json`
that `fit` wrote - and `fit` filters to `split == 'calibration'` at read time and
raises if anything else survives. As a second, independent check the loop asserts
that every target id appearing in a fit block is in the calibration set *as
reported by fit itself*, so a leak would have to defeat both.

**It cannot move a parameter it is not allowed to move.** The search space is
derived from the registry, not listed here: a field is free only if it is
`assumed`, carries a numeric sweep interval, and is NOT `held_fixed`. A field
held fixed under DECISIONS.md 8.5 is unreachable from this loop by
construction, which is the whole point of 8.5 - proposal 9 names ASC absorption
as the primary threat to validity.

**It optimises the goal the project actually states.** The objective is
`goal_modes.max_abs_rel_pct`: the MAXIMUM absolute deviation, in RELATIVE per
cent, over the twelve modes of `mode_targets_by_mode.csv`, computed by calling
the board's own reader so the objective and the gate cannot drift apart. It was
`mode_share.mean_abs_pp`, a MEAN over FIVE FOLDED survey categories in
PERCENTAGE POINTS, and the two are different measurement systems: heavy rail
and light rail sit inside one folded "Public transport" cell with OPPOSITE
signs, so a search minimising the fold could improve its own objective while
making both modes worse. Measured at the moment of the change, on one real run:
the folded objective read 11.18 pp on a model whose heavy rail was +471.7%.

**It refuses to fit more parameters than the data identifies.** The objective
contains ten independent numbers (twelve modes, less truck - scored on a basis
that is not the target's own ground - and less freight rail, a representation
rather than a fit). A search over more free parameters than that is not a
calibration, and the loop exits rather than producing one. That refusal is the
loop working, not failing: it names the movable set and asks for a subset with
a stated reason.

**A stage it claims it can carry out, it carries out.** A `run_inputs`-stage
field is only real once the assembled set carries it - the runner runs a set
out of `scenarios/matsim/`, it does not re-derive one - so `evaluate()`
re-assembles the scenario x day per candidate, from the ALREADY-MAPPED schedule
only, and restores the shipped assembly when the search ends. The stage was
listed as implemented and carried out by nothing, so such a candidate ran the
shipped value and the search compared a parameter against itself.

**It does not calibrate against traffic counts.** DECISIONS.md 9.14 and 9.15:
the external tier carries no through traffic, so every boundary-adjacent count is
biased low by construction and tuning the core network against them would be
compensating for absent demand. Counts are still scored and reported on every
run - they are simply not optimised against. `CAL.objective.include_counts`
holds the rule and the loop enforces it.

**Constraints are constraints, not targets.** The occupancy and trip-length
constraints (C4) never enter the objective; a candidate that violates one is
marked infeasible and reported. Adding an observable to the objective would make
it a target, and the 67/143 split is pre-registered.

    python src/calibrate/calibrate.py --scenario S2 --day WEEKDAY \
        --run-config cordon_escort_10pct --plan
    python src/calibrate/calibrate.py --scenario S2 --day WEEKDAY \
        --run-config cordon_escort_10pct --execute
"""

# City-relative paths resolve through src/city.py: `data/...` names a
# location inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', 'src'))
import city as _city  # noqa: E402

# a run name resolves through the results store - results/raw first, then a
# legacy top-level dir - so consumers survived the 9.137 layout change once,
# here, instead of each composing its own results/ path
import sys as _sys_rs, os as _os_rs
_sys_rs.path.insert(0, _os_rs.path.join(_os_rs.path.dirname(
    _os_rs.path.dirname(_os_rs.path.abspath(__file__))), 'run'))
import results_store as _results_store  # noqa: E402
# the runner owns run identity: `find_completed` is what resume
# already trusts, and this loop must not keep a second opinion
import run_matsim as _run_matsim  # noqa: E402


def _resolve_run(name_or_path):
    return _results_store.resolve(name_or_path) or name_or_path


import os
import sys
import json
import argparse
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import registry as _registry                                    # noqa: E402

OUT = _city.path('params/C5_calibration.json')


# What a candidate has to REBUILD before a change to a field is real. The loop
# runs run_matsim -> extract_metrics -> fit and rebuilds nothing else, so a field
# whose only consumer is a build script cannot be realised by passing --set: that
# would change the recorded configuration without changing a single input, which
# is worse than not calibrating it at all.
#
# `forbidden` is not about cost. DECISIONS.md 3.5: re-running the pt2matsim
# mapper changes ~18% of route link sequences, so a scenario mapped in one build
# cannot be compared with one mapped in another. Those fields are uncalibratable
# inside a comparison, whatever their sweep says.
STAGE_OF_CONSUMER = {
    'build_matsim_network.py': 'forbidden',
    'build_scenario_schedules.py': 'forbidden',
    'build_sumo_corridor.py': 'forbidden',
    'build_corridor_road_attributes.py': 'forbidden',
    'build_era1_reconstruction.py': 'forbidden',
    'build_gtfs_extras.py': 'forbidden',
    'shape_tools.py': 'forbidden',
    'build_activity_chains.py': 'demand',
    'build_population.py': 'demand',
    'build_matsim_plans.py': 'demand',
    'build_landuse_parking.py': 'demand',
    'build_zone_attractions.py': 'demand',
    'build_matsim_run_inputs.py': 'run_inputs',
    # The emitter builds the config FROM the registry at run time, so a field it
    # consumes needs NO rebuild to vary - run_matsim.py emits per run rather
    # than patching six parameters into a shipped file. More fields are
    # calibratable than were, and this is where that shows.
    'param_config.py': 'none',
}
MEASUREMENT_LAYERS = ('src/analyse/', 'src/calibrate/')
# Stages this loop can actually carry out for a candidate.
STAGES_IMPLEMENTED = ('none', 'run_inputs')


_DERIVED_REALISERS = None


def derived_realisers():
    """Fields that reach the config through ANOTHER field's `derived_from`.

    Maps a child key to the parent whose binding realises it. Built once from
    the registry: a parent qualifies when it carries a `matsim_param` (so it
    reaches the config on every run) and its `derived_from.fields` names the
    child. The DERIVATION is the evidence, exactly as the BINDING is in
    `rebuild_stage` - a conservative default over a NAME is right, a
    conservative default over a DECLARED IDENTITY is wrong for the same reason.
    """
    global _DERIVED_REALISERS
    if _DERIVED_REALISERS is not None:
        return _DERIVED_REALISERS
    out = {}
    try:
        import glob as _glob
        pattern = os.path.join(_city.CITY_DIR, 'registry', '*.json')
        for path in sorted(_glob.glob(pattern)):
            with open(path, encoding='utf-8') as fh:
                fields = json.load(fh).get('fields', {})
            for parent, spec in fields.items():
                if not spec.get('matsim_param'):
                    continue
                derived = spec.get('derived_from') or {}
                for child in (derived.get('fields') or []):
                    out.setdefault(child, parent)
    except Exception:                                          # noqa: BLE001
        # A registry this cannot read is one `rebuild_stage` should stay
        # conservative about, not one it should guess for.
        out = {}
    _DERIVED_REALISERS = out
    return out


def rebuild_stage(key, field):
    """What a change to this field would require. 'none' means run-time only."""
    if key.startswith('CAL.'):
        return 'excluded', "the loop's own search controls"
    if key.startswith('RUN.'):
        return 'excluded', ('run identity and compute, not a property of %s'
                            % _city.descriptor()['name'])
    stage, why = 'none', None
    consumers = field.get('consumers') or []
    for c in consumers:
        if any(c.startswith(m) for m in MEASUREMENT_LAYERS):
            return 'excluded', ('consumed by %s: measurement apparatus, not the '
                                'model' % c)

    # A field carrying a `matsim_param` binding is EMITTED INTO THE CONFIG AT
    # RUN TIME by src/registry/param_config.py, whatever else lists itself as a
    # consumer. That makes it run-time realisable by definition, and the
    # consumer table must not be able to say otherwise.
    #
    # This is the half of the movable set the table was silently eating. The
    # lookup below keys on a consumer's BASENAME and excludes anything it does
    # not recognise - a deliberately conservative default, and the right one,
    # because the permissive default once put the OSM harvest margins in the
    # movable set. But a field whose declared consumer is a Java config group
    # (`GradientConfigGroup.java`) or which declares no consumer at all was
    # excluded as "would reach nothing" while carrying a binding that reaches
    # the config on every single run. Four scalar swept fields with real
    # bindings were excluded that way, which is how a search space of 482
    # declared fields collapsed to five.
    #
    # The binding is the evidence. A conservative default over a NAME is right;
    # a conservative default over a DECLARED BINDING is just wrong.
    if field.get('matsim_param'):
        return 'none', None

    # ... and a field REACHED THROUGH one. `C.asc.bus` carries no consumer and
    # no binding of its own; it reaches `scoring.modeParams[*].constant`
    # through `C.scoring.mode_constant`'s `derived_from.fields`. Excluding it
    # as "nothing would read a change" is false - the derivation reads it on
    # every run - and it is why the 8.5 departure logged at 9.158, taken so a
    # search could reach `C.asc.bus` and `C.asc.light_rail`, bought the search
    # nothing.
    parent = derived_realisers().get(key)
    if parent:
        return 'none', None

    for c in consumers:
        st = STAGE_OF_CONSUMER.get(c.rsplit('/', 1)[-1])
        if st == 'forbidden':
            return 'forbidden', ('consumed by %s: realising it needs the '
                                 'schedule mapper re-run, which 3.5 forbids '
                                 'inside a comparison' % c)
        if st is None:
            # A consumer this table does not classify gets EXCLUDED, not
            # defaulted to run-time-realisable. The permissive default put the
            # OSM harvest margins and the speed-zone clip radius in the movable
            # set: a --set on any of them would be validated, recorded in the
            # run's provenance snapshot, and change nothing the run reads -
            # this repository's signature defect, inside the one tool whose
            # job is to move values that reach the model.
            return 'excluded', ('consumed by %s, which the rebuild-stage table '
                                'does not classify; a run-time override would '
                                'be recorded and reach nothing' % c)
        if st == 'demand' and stage != 'demand':
            stage, why = 'demand', ('consumed by %s: needs B2, the plans and the '
                                    'run inputs rebuilt per candidate' % c)
        elif st == 'run_inputs' and stage == 'none':
            stage, why = 'run_inputs', 'needs the 30 run-input sets regenerated'
    if not (field.get('consumers') or []):
        return 'excluded', 'no declared consumer: nothing would read a change'
    return stage, why


def excluded_reason(key, field):
    """Why a field with a sweep is still not calibratable. None if it is."""
    stage, why = rebuild_stage(key, field)
    if stage in STAGES_IMPLEMENTED:
        return None
    return why or ('needs the %s rebuild, which this loop does not carry out'
                   % stage)


def free_parameters(cfg, report=None):
    """Registry fields this loop is permitted to move, derived not listed."""
    free = []
    for key in sorted(cfg.keys()):
        f = cfg.field(key)
        if f.get('status') != 'active':
            continue
        if f.get('source') != 'assumed':
            continue                      # measured/derived/definition are not ours
        if 'held_fixed' in f:
            continue                      # DECISIONS.md 8.5 and friends
        lo, hi = sweep_interval(f)
        if lo is None or not isinstance(f.get('value'), (int, float)):
            continue                      # dict- or list-valued sweeps are not scalar
        why = excluded_reason(key, f)
        if why:
            if report is not None:
                report.append((key, why))
            continue
        stage, _ = rebuild_stage(key, f)
        free.append(dict(key=key, value=float(f['value']), lo=lo, hi=hi,
                         units=f.get('units'), stage=stage,
                         decisions_ref=f.get('decisions_ref')))
    return free


def sweep_interval(field):
    """(lo, hi) if the field carries a scalar sweep, else (None, None)."""
    s = field.get('sweep')
    if isinstance(s, list) and len(s) == 2 and all(
            isinstance(v, (int, float)) for v in s):
        return float(s[0]), float(s[1])
    if isinstance(s, dict):
        iv = s.get('interval')
        if isinstance(iv, list) and len(iv) == 2:
            return float(iv[0]), float(iv[1])
        p = s.get('proportional')
        v = field.get('value')
        if isinstance(p, (int, float)) and isinstance(v, (int, float)):
            return v * (1.0 - p), v * (1.0 + p)
    return None, None


def objective(fit, components, band_pp):
    """Scalar objective from a fit block. A missing component is an error.

    ``band_pp`` is the REPLICATION BAND (DECISIONS.md 9.164, #163): the spread
    a component takes across runs of the SAME configuration, in the component's
    own units. A MATSim run is not bit-reproducible - within
    ``20260909T015217_300it_25pct``, with nothing changed, the folded objective
    moves 0.272-0.418 pp between iterations 80 and 100 - so some part of every
    deviation this loop chases is seed scatter, and a search that chases it is
    fitting noise.

    The form is the one history matching uses. Its implausibility statistic is
    ``|observed - modelled|`` over a denominator that includes model
    discrepancy and observational noise; this objective was a bare maximum over
    twelve modes with NO DENOMINATOR AT ALL. Dividing by the band makes the
    objective count HOW MANY BANDS OUT a mode is, so a deviation inside the
    noise scores below one and stops being worth an arm.

    A band of zero divides by nothing: the objective is the raw maximum,
    exactly as before, and that is the value
    ``CAL.objective.replication_band_pp`` ships at. **THE BAND MUST BE MEASURED
    BEFORE IT IS SET.** Inventing a denominator would be precisely the failure
    this project cannot absorb, which is why the field that carries it ships at
    zero and why this function refuses a negative one rather than taking its
    absolute value. There is deliberately NO DEFAULT on this argument: a
    default here would be the same value decided in two places, and every
    caller reads it from the registry through :func:`replication_band`.
    """
    if band_pp < 0.0:
        raise SystemExit(
            'the replication band is %r. A negative band is not a spread; it '
            'is a sign error that would flip the objective. It is declared as '
            'CAL.objective.replication_band_pp.' % band_pp)
    total = 0.0
    parts = {}
    for path, weight in sorted(components.items()):
        node = fit
        for bit in path.split('.'):
            if not isinstance(node, dict) or bit not in node:
                raise SystemExit(
                    'objective component %r is not in the fit output. The loop '
                    'will not treat a missing component as zero - that would '
                    'silently optimise something other than what was declared.'
                    % path)
            node = node[bit]
        if not isinstance(node, (int, float)):
            raise SystemExit('objective component %r is not a number' % path)
        parts[path] = node
        total += weight * (float(node) / band_pp if band_pp > 0.0
                           else float(node))
    return total, parts


def replication_band(cfg):
    """The declared replication band, and the note that goes with it."""
    band = float(cfg.get('CAL.objective.replication_band_pp'))
    note = ('none - the objective is the raw maximum, and no deviation on the '
            'board carries an error bar (#163)' if band <= 0.0 else
            'CAL.objective.replication_band_pp = %g: the objective counts how '
            'many bands out the worst mode is' % band)
    return band, note


def feasible(fit):
    """C4 constraints. Violations make a candidate infeasible, never scored."""
    why = []
    occ = fit.get('occupancy_constraint') or {}
    if occ and not occ.get('inside_observed_range', True):
        why.append('vehicle occupancy %.4f passengers/driver is outside the '
                   'observed range %s'
                   % (occ.get('modelled_passenger_per_driver', float('nan')),
                      occ.get('observed_sweep')))
    tg = fit.get('trip_geometry_constraint') or {}
    for mode, g in sorted((tg.get('modes') or {}).items()):
        if not g.get('inside_observed_range', True):
            why.append('%s trip length %.2f km is outside the observed range'
                       % (mode, g.get('modelled_mean_distance_km', float('nan'))))
    return (not why), why


def audit_no_holdout(fit):
    """Second, independent check that no holdout row reached the objective."""
    avail = fit.get('calibration_targets_available')
    if not isinstance(avail, int):
        raise SystemExit('fit output does not state how many calibration '
                         'targets were available; refusing to optimise on it')
    scored, unscorable = fit.get('scored'), fit.get('unscorable')
    if scored is None or unscorable is None:
        raise SystemExit('fit output does not reconcile scored against '
                         'explained; refusing to optimise on it')
    if scored + len(unscorable) != avail:
        raise SystemExit('fit output does not reconcile: %s scored + %s '
                         'explained != %s available'
                         % (scored, len(unscorable), avail))
    for block in ('mode_share', 'patronage', 'counts'):
        b = fit.get(block) or {}
        if b.get('n') and not b.get('targets'):
            raise SystemExit('fit block %r scored %s targets without naming '
                             'them; a statistic that does not name its targets '
                             'is not reportable' % (block, b.get('n')))
    # THE GOAL-MODES BLOCK READS NO STATION-LEVEL ROW (#189, 12 September
    # 2026). The heavy-rail per-mode target is a SUM over the station
    # publication whose per-station MEANS are the pre-registered holdout;
    # the sum is the calibration observation and the means stay shut. This
    # asserts the block names no target id at all - its rows come from
    # mode_targets_by_mode.csv, never from validation_targets.csv - so a
    # future reader that scored a station mean here would be refused.
    holdout_ids = set()
    try:
        import csv as _csv                                     # noqa: PLC0415
        with open(_city.path('data/processed/validation/validation_targets.csv'),
                  encoding='utf-8') as fh:
            holdout_ids = {r['target_id'] for r in _csv.DictReader(fh)
                           if r.get('split') == 'holdout'}
    except OSError:
        pass
    for row in (fit.get('goal_modes') or {}).get('modes') or []:
        named = {row.get('target_id')} | set(row.get('target_ids') or [])
        hit = sorted(t for t in named if t and t in holdout_ids)
        if hit:
            raise SystemExit('goal_modes row %r scores holdout target(s) %s: '
                             'the twelve-mode objective may sum a disclosed '
                             'publication but may never read a pre-registered '
                             'holdout row (DECISIONS.md 12, #189)'
                             % (row.get('mode'), hit))


def grid(p, n):
    """n points across a parameter's sweep, endpoints included, current kept."""
    if n < 2:
        return [p['value']]
    step = (p['hi'] - p['lo']) / (n - 1)
    pts = [p['lo'] + i * step for i in range(n)]
    if not any(abs(x - p['value']) < 1e-12 for x in pts):
        pts.append(p['value'])
    return sorted(set(round(x, 10) for x in pts))


def candidate_tag(base, key, value):
    short = key.replace('.', '_')
    return '%s__%s_%g' % (base, short, value)


def write_constrained_base(scenario, day, run_config, tag):
    """C5 under the 8.5 SECOND branch: constrain and report (DECISIONS.md 9.50).

    No search ran and none is pretended: `free_parameters` is empty,
    `calibrated` is empty, and the record points at ONE run of the current
    demand family whose fit is reported exactly as fit.py wrote it. The mode
    constants stay at their 8.5 priors (held_fixed, unreachable from the loop
    by construction); `asc_car_passenger` is NOT re-solved against the 9.48
    occupancy excess - that would absorb a modelled defect into a constant,
    the ASC-absorption move proposal 9 names as the primary threat - and the
    excess is carried here as a stated constraint violation instead.
    """
    cfg = _registry.load(scenario=scenario, day=day, run=run_config)
    run_dir = _resolve_run(tag)
    fit_path = os.path.join(run_dir, '_fit.json')
    if not os.path.exists(fit_path):
        raise SystemExit('no _fit.json in %s - the base run must exist and be '
                         'fitted before C5 can report it' % run_dir)
    record_path = os.path.join(run_dir, '_run.json')
    if not os.path.exists(record_path):
        raise SystemExit('%s has no _run.json: a run without one is not a '
                         'result and cannot anchor the calibrated base' % run_dir)
    # PRESENCE IS NO LONGER THE TEST. A run stopped at a GOAL.md gate is closed
    # out with a record too, and its reading is real - but it is a reading at
    # the iteration the gate fired on, not a run that reached the horizon it
    # declared, and a base calibrated on one would state a converged model the
    # run never produced. Records written before the field existed were only
    # ever written on rc=0, so a missing value reads as ran_to_last_iteration.
    done = json.load(open(record_path, encoding='utf-8')).get(
        'completion', 'ran_to_last_iteration')
    if done != 'ran_to_last_iteration':
        raise SystemExit(
            '%s was %s and did not reach its last iteration: its reading is '
            'citable but it is not a complete arm, and it cannot anchor the '
            'calibrated base' % (run_dir, done))
    f = json.load(open(fit_path, encoding='utf-8'))
    audit_no_holdout(f)
    ok, why = feasible(f)
    comps = cfg.get('CAL.objective.components')
    band, band_note = replication_band(cfg)
    obj, parts = objective(f, comps, band)
    excluded = []
    free = free_parameters(cfg, excluded)
    result = dict(
        generated=datetime.datetime.now(datetime.timezone.utc)
        .strftime('%Y-%m-%dT%H:%M:%SZ'),
        scenario=scenario, day=day, run_config=run_config,
        branch='constrain-and-report (DECISIONS.md 8.5 second branch, 9.50)',
        decisions_ref='9.50',
        objective_components=comps,
        replication_band_pp=band,
        replication_band=band_note,
        independent_targets=int(cfg.get('CAL.objective.independent_targets')),
        free_parameters=[],
        search_declined=dict(
            movable={p['key']: dict(value=p['value'], lo=p['lo'], hi=p['hi'])
                     for p in free},
            reason='the loop can legitimately move only these parameters, at '
                   '~21 full 25% x 1000 runs; neither reaches the structural '
                   'misfits (9.25, 9.28), so the search was DECLINED with the '
                   'cost stated rather than run for its appearance (9.50)'),
        best_tag=tag, best_objective=obj, objective_parts=parts,
        calibrated={},
        constraints=dict(feasible=ok, violations=why),
        history=[],
        note='CONSTRAINED, not fitted (DECISIONS.md 9.50). Every parameter '
             'kept its declared registry value; the mode constants stay at '
             'their 8.5 priors, held fixed; asc_car_passenger is NOT re-solved '
             'against the 9.48 occupancy excess, which is reported above as a '
             'constraint violation instead of being absorbed. The fit is one '
             'reference run of the 9.49 demand family, reported as it came '
             'out. Counts were scored, not optimised against (9.14). No '
             'holdout row was read.')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # newline='\n': see the identical note at the search writer below - a
    # default-mode Windows write breaks CI's manifest integrity on this
    # committed, hashed file.
    json.dump(result, open(OUT, 'w', newline='\n'), indent=2)
    print('constrained base from %s (objective %.4f, feasible=%s) -> %s'
          % (tag, obj, ok, OUT))
    for v in why:
        print('   stated violation: %s' % v)


def _best_run_dir(tag):
    """The results-store directory a run tag resolves to, or None."""
    try:
        import results_store                                  # noqa: PLC0415
        d = results_store.resolve_records(tag)
        return os.path.basename(os.path.normpath(d)) if d else None
    except Exception:                                         # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # the CITY's base scenario and first day type, not ids typed here
    ap.add_argument('--scenario',
                    default=_city.descriptor()['intervention']['base_scenario'])
    ap.add_argument('--day', default=list(_city.descriptor()['day_types'])[0])
    ap.add_argument('--run-config', required=True,
                    help='committed overlay giving fraction, iterations, threads')
    ap.add_argument('--plan', action='store_true',
                    help='print the search and its cost, run nothing')
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--constrained-base', metavar='TAG',
                    help='write C5 from an existing run under the 8.5 '
                         'constrain-and-report branch (DECISIONS.md 9.50): '
                         'no search, every parameter keeps its declared value, '
                         'the named run\'s fit is reported as it came out')
    ap.add_argument('--only', action='append', default=None,
                    help='restrict the free set to these registry keys')
    a = ap.parse_args()
    if not (a.plan or a.execute or a.constrained_base):
        raise SystemExit('choose --plan, --execute or --constrained-base')

    if a.constrained_base:
        write_constrained_base(a.scenario, a.day, a.run_config,
                               a.constrained_base)
        return

    cfg = _registry.load(scenario=a.scenario, day=a.day, run=a.run_config)
    comps = cfg.get('CAL.objective.components')
    if cfg.get('CAL.objective.include_counts'):
        raise SystemExit(
            'CAL.objective.include_counts is true. DECISIONS.md 9.14 forbids '
            'count-based calibration while boundary through traffic is '
            'unrepresented. Record a departure there before setting it.')
    n_free_allowed = int(cfg.get('CAL.objective.independent_targets'))
    ppp = int(cfg.get('CAL.search.points_per_parameter'))
    max_rounds = int(cfg.get('CAL.search.max_rounds'))
    delta = float(cfg.get('CAL.search.convergence_delta'))
    reading_drift = float(cfg.get('CAL.search.reading_drift_pct'))
    pass_band = float(cfg.get('CAL.gate.pass_deviation_pct'))

    excluded = []
    free = free_parameters(cfg, excluded)
    if a.only:
        keep = set(a.only)
        free = [p for p in free if p['key'] in keep]
        missing = keep - {p['key'] for p in free}
        if missing:
            raise SystemExit('not free parameters (measured, held fixed, or no '
                             'scalar sweep): %s' % ', '.join(sorted(missing)))

    # Does any candidate need the run inputs re-assembled? A `run_inputs`-stage
    # field is not realised by an override alone - the runner runs a set that
    # was assembled earlier - so the loop must rebuild that set per candidate.
    needs_run_inputs = any(p['stage'] == 'run_inputs' for p in free)

    print('%d registry fields are movable by this loop (assumed, scalar sweep, '
          'not held fixed, not excluded).' % len(free))
    print('%d were excluded with a reason:' % len(excluded))
    for k, why in excluded:
        print('   %-46s %s' % (k, why))
    print('The objective contains %d independent numbers.' % n_free_allowed)
    if len(free) > n_free_allowed:
        print('\nA search over all of them would fit %d parameters to %d '
              'numbers.' % (len(free), n_free_allowed))
        print('Name at most %d with --only. The movable set is:'
              % n_free_allowed)
        for p in free:
            print('   %-46s %10.5g  sweep %.5g - %.5g  [%s]'
                  % (p['key'], p['value'], p['lo'], p['hi'], p['units']))
        raise SystemExit(
            '\nrefusing to fit %d parameters to %d independent numbers: that is '
            'not a calibration. Choose a subset with --only, on a stated reason.'
            % (len(free), n_free_allowed))

    evals = sum(len(grid(p, ppp)) for p in free) * max_rounds
    print('\nsearch: coordinate descent, %d parameter(s), %d point(s) each, '
          'up to %d round(s)' % (len(free), ppp, max_rounds))
    print('objective: %s' % ', '.join('%s x%.3g' % (k, v)
                                      for k, v in sorted(comps.items())))
    print('at most %d run(s); each is a full MATSim run at the overlay settings'
          % evals)
    for p in free:
        print('   %-46s start %10.5g   points %s   [%s]'
              % (p['key'], p['value'],
                 ', '.join('%g' % x for x in grid(p, ppp)), p['stage']))
    if needs_run_inputs:
        print('at least one parameter is run_inputs-staged, so each candidate '
              're-assembles %s x %s from the ALREADY-MAPPED schedule before it '
              'runs (3.5: the mapper is never re-run inside a comparison). The '
              'shipped assembly is restored when the search ends.'
              % (a.scenario, a.day))
    # THE READING POINT HAS TO BE ABLE TO RESOLVE THE ANSWER.
    #
    # A gate reading is taken at one iteration, and iteration 100 was adopted
    # as that point on COST - it was never once tested for stability. It has now
    # been measured, within-run, on all six 25% arms that ever reached it: the
    # objective moves CAL.search.reading_drift_pct between iteration 80 and 100
    # OF THE SAME RUN, with nothing changed at all. If that drift is larger than
    # the band the goal asks a mode to sit inside, then a reading there cannot
    # decide whether a mode is inside the band - let alone which of two
    # candidates is better - and a search scored on it would be ranking noise.
    #
    # This refuses rather than warns. A search that cannot resolve its own
    # objective produces a `calibrated` block and a `best_tag` that look exactly
    # like a result, which is the one failure this project cannot absorb.
    print('\nreading point: the objective drifts %.4g%% between iteration 80 '
          'and 100 WITHIN one run (%d arms measured), against a pass band of '
          '%.4g%%' % (reading_drift, 6, pass_band))
    if reading_drift > pass_band:
        print('\nA reading at this point cannot decide whether a mode is inside '
              'the %.4g%% band: the reading moves further than the band by '
              'itself.' % pass_band)
        if a.execute:
            raise SystemExit(
                'refusing to search on a reading that cannot resolve the goal '
                'band. Lower CAL.search.reading_drift_pct by changing the '
                'READING, not the rule - read deeper than iteration 100, or '
                'average a window of iterations instead of taking a point - and '
                're-measure with src/analyse/measure_reading_stability.py. '
                'Until then a search would rank noise and hand back a '
                'best_tag that looks like a result.')
        print('--plan continues so the search can be costed, but --execute is '
              'refused until the reading resolves the band.')

    if a.plan:
        print('\n--plan: nothing was run.')
        return

    import subprocess

    history, current = [], {p['key']: p['value'] for p in free}
    best_obj, best_tag = None, None
    base = 'cal_%s_%s_%s' % (a.scenario, a.day, a.run_config)

    def find_run(overrides):
        """The completed run this candidate's overrides produced, if any.

        DELEGATED, and deliberately so. This was a hand-rolled glob matching
        `_run.json`'s `overrides` - the RAW MATSim `--set` channel - while
        `evaluate()` sends its candidate through `--config-set`, the REGISTRY
        channel. A candidate therefore recorded `overrides: {}`, never matched,
        and the loop raised AFTER paying a full arm's wall clock. The copy also
        missed `results/processed/`, where the store keeps findings for ever,
        and accepted any record with `rc == 0`, so an arm stopped at its gate
        could have become the calibrated base the README is drawn from.

        `run_matsim.find_completed` answers all three and is the function resume
        already trusts: it searches RAW, PROCESSED and RESULTS, it requires
        `completion == ran_to_last_iteration` (9.143), and it compares
        `values_sha256`, the fingerprint of every resolved registry value, which
        is precisely what distinguishes one `--config-set` candidate from
        another (9.104). A candidate is still located by what was actually run
        and never by a name this loop invented - the same rule, now enforced by
        the code that owns it.
        """
        cand = _run_matsim.resolve(a.scenario, a.day, a.run_config, overrides)
        rec = _run_matsim.find_completed(
            a.scenario, a.day,
            cand.get('RUN.sample.fraction'),
            cand.get('RUN.controler.last_iteration'),
            cand.get('RUN.machine.seed'),
            {},                    # this loop sends no raw `--set` overrides
            values=_run_matsim.values_sha256(cand))
        if not rec:
            return None
        # the record names the directory that actually holds it; the store
        # knows where that is, whether raw or processed
        return _results_store.resolve(rec['name'])

    def rebuild_run_inputs(overrides):
        """Re-assemble this scenario x day's run inputs under the candidate.

        A `run_inputs`-stage field (a mode constant, the gradient clamp) is only
        real once the assembled set carries it: `run_matsim.py` runs a set out
        of `scenarios/matsim/<S>/<DAY>/`, it does not re-derive one. The loop
        listed `run_inputs` in STAGES_IMPLEMENTED and then never carried it
        out, so such a candidate ran the SHIPPED value and the search compared
        a parameter against itself.

        This re-assembles ONLY the scenario and day under test, and only from
        the ALREADY-MAPPED schedule - `build_matsim_run_inputs.py` filters
        `transitRoute` ids off the existing mapping and never re-runs the
        pt2matsim mapper, which DECISIONS.md 3.5 forbids inside a comparison.
        Fields whose consumer DOES need the mapper are `forbidden`, not
        `run_inputs`, and never reach here.

        It writes into the committed, manifest-hashed assembled set, so the
        caller restores the shipped assembly when the search ends.
        """
        r = subprocess.run(
            [sys.executable, 'src/build/build_matsim_run_inputs.py',
             '--scenarios', a.scenario, '--day-types', a.day]
            + [x for k, v in sorted(overrides.items())
               for x in ('--set', '%s=%s' % (k, v))])
        if r.returncode != 0:
            raise SystemExit('build_matsim_run_inputs.py failed (%d) while '
                             'assembling a candidate' % r.returncode)

    def evaluate(label, overrides):
        """One candidate: assemble if needed, run, extract, fit, score.

        Resumable by its overrides.
        """
        # the declared pipeline, invoked exactly as a reader would by hand:
        # build_matsim_run_inputs.py -> run_matsim.py -> extract_metrics.py -> fit.py
        run_dir = find_run(overrides)
        if run_dir is None:
            if needs_run_inputs:
                rebuild_run_inputs(overrides)
            # `--config-set`, NOT `--set`. They are different channels and the
            # loop was using the wrong one: `--config-set` takes a REGISTRY key,
            # validates it against its declared sweep and refuses a held-fixed
            # field; `--set` takes a RAW MATSim config key and
            # `build_config` splits it on its first dot, so a registry key
            # arriving there raised inside `set_mode_param` and the search died
            # on its first candidate. `--execute` had therefore never completed
            # one. The correct channel was always 40 lines away in
            # solve_asc_ride.py, which resolves through the registry.
            sets = []
            for k, v in sorted(overrides.items()):
                sets += ['--config-set', '%s=%s' % (k, v)]
            r = subprocess.run([sys.executable, 'src/run/run_matsim.py',
                                '--scenario', a.scenario, '--day', a.day,
                                '--run-config', a.run_config] + sets)
            if r.returncode != 0:
                raise SystemExit('run_matsim.py failed (%d) for candidate %s'
                                 % (r.returncode, label))
            run_dir = find_run(overrides)
            if run_dir is None:
                raise SystemExit('candidate %s ran but no completed run record '
                                 'carries its overrides' % label)
        name = os.path.basename(run_dir)
        fit_path = os.path.join(run_dir, '_fit.json')
        if not os.path.exists(fit_path):
            for step in ('src/analyse/extract_metrics.py', 'src/calibrate/fit.py'):
                r = subprocess.run([sys.executable, step, '--run', name])
                if r.returncode != 0:
                    raise SystemExit('%s failed (%d) for candidate %s'
                                     % (step, r.returncode, label))
        f = json.load(open(fit_path, encoding='utf-8'))
        audit_no_holdout(f)
        obj, parts = objective(f, comps, replication_band(cfg)[0])
        ok, why = feasible(f)
        rec = dict(tag=name, candidate=label, overrides=dict(overrides),
                   objective=obj, components=parts, feasible=ok,
                   constraint_violations=why)
        history.append(rec)
        print('   %-58s obj %8.4f %s' % (label, obj, '' if ok else '  INFEASIBLE'))
        return rec

    try:
        for rnd in range(max_rounds):
            print('\nround %d' % (rnd + 1))
            start = best_obj
            for p in free:
                for value in grid(p, ppp):
                    ov = dict(current)
                    ov[p['key']] = value
                    rec = evaluate(candidate_tag(base, p['key'], value), ov)
                    if rec['feasible'] and (best_obj is None
                                            or rec['objective'] < best_obj):
                        best_obj, best_tag = rec['objective'], rec['tag']
                        current[p['key']] = value
            if start is not None and best_obj is not None and start - best_obj < delta:
                print('round improved the objective by %.4f < %.4f: stopping'
                      % (start - best_obj, delta))
                break
    finally:
        # The assembled sets are COMMITTED and MANIFEST-HASHED. A search that
        # rebuilt them per candidate leaves the tree holding the last
        # candidate's values, which would show up as an unexplained manifest
        # drift in whatever session came next. Restore the shipped assembly
        # whatever happened - including on a failure or a Ctrl-C, which is why
        # this is a finally and not a line at the end.
        if needs_run_inputs:
            print('\nrestoring the shipped assembly for %s x %s'
                  % (a.scenario, a.day))
            rebuild_run_inputs({})

    result = dict(
        generated=datetime.datetime.now(datetime.timezone.utc)
        .strftime('%Y-%m-%dT%H:%M:%SZ'),
        scenario=a.scenario, day=a.day, run_config=a.run_config,
        objective_components=comps,
        independent_targets=n_free_allowed,
        free_parameters=[p['key'] for p in free],
        best_tag=best_tag, best_objective=best_obj,
        # the runner's directory name for the best run, beside the tag the
        # record carries (#137): the tag is what the run called itself, the
        # directory is what the store calls it
        best_run=_best_run_dir(best_tag),
        calibrated=current, history=history,
        note='Calibrated against the CALIBRATION half only. Counts were scored '
             'and reported but not optimised against (DECISIONS.md 9.14). The '
             'C4 constraints were feasibility conditions, never targets.')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # newline='\n': C5 is committed and manifest-hashed; a Windows default-mode
    # write puts CRLF in the working tree, the manifest hashes those bytes, and
    # CI (which checks out the gitattributes-normalised LF bytes) then fails
    # manifest integrity - measured on PR #67.
    json.dump(result, open(OUT, 'w', newline='\n'), indent=2)
    print('\nbest %s at objective %.4f -> %s' % (best_tag, best_obj, OUT))


if __name__ == '__main__':
    main()
