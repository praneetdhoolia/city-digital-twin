#!/usr/bin/env python
"""One round of the alternative-specific-constant fixed point. PROPOSES ONLY.

**What this is for.** Eight of twelve modes have sat outside their target band
for eleven comparability families, and the project has never established WHY:
whether the residual is a taste the mode constants have simply not been set to,
or a mechanism the model does not contain. Those two have opposite remedies and
look identical on the board. This settles it, cheaply, in two rounds.

**The test is the CONTRACTION, not the shares.** Apply one damped step, run,
apply a second, and compare the two steps mode by mode. If |delta| shrinks, the
map is a contraction and the residual really is a constant - the shares will
close if the rounds continue. If |delta| does not shrink, no constant will ever
close it and the deficit is structural. Either answer ends the question. Read
`round_over_round` in the proposal, not the mode shares.

**The update rule.** For mode i against the reference mode (car), the step is

    delta_i = damping * [ ln(target_i / modelled_i)
                          - ln(target_ref / modelled_ref) ]

which is the contraction a multinomial logit's share equation implies, and the
same object as the Berry (1994) inversion of shares onto constants. It is what
`matsim-vsp/matsim-python-tools` computes verbatim and what the ActivitySim
agency practice applies with a flat dampener; both are recorded on
`CAL.asc.damping`. The ratio is taken from the board's own `deviation_pct`
(modelled/target = 1 + dev/100), so this loop and the gate read one number.

**On the two boarding-basis modes, the step is a PROXY and says so.** The logit
inversion above is exact for a mode stated as a SHARE of the same total. Heavy
rail and light rail are stated as weekday BOARDINGS, so their ratio is
monotone in the right direction and of the right order, but it is not the exact
contraction. The proposal marks those rows `basis_is_boardings` and the
contraction verdict is reported with and without them.

**THE HONEST TENSION, stated rather than smuggled past.** `.claude/CLAUDE.md`
bans compensating constants and DECISIONS.md 8.5 freezes the mode constants
because proposal 9 names ASC absorption as the primary threat to validity. An
ASC fixed point is, definitionally, fitting mode constants to observed shares.
That ban is RIGHT for a mode whose deviation has a NAMED missing mechanism -
heavy rail has no crowding disutility in scoring at all, so a rail constant
would price a physical omission into a taste parameter - and it is right for a
mode whose deficit is in plan generation rather than scoring, as ride's is. It
is over-broad for a mode with no such named absence, whose constant is an
ordinary ASC of the kind every eqasim, ActivitySim and Open Berlin model fits.
This loop therefore CANNOT reach a frozen constant: it reads `held_fixed` from
the registry and refuses, structurally, the way the holdout guard refuses. Which
modes are open is a decision recorded in the registry with a per-mode reason,
not a decision this file makes.

    python src/calibrate/asc_fixed_point.py --run <run> --out round1.json
    python src/calibrate/asc_fixed_point.py --run <run> --previous round1.json
"""

import city as _city

import results_store as _results_store

import registry as _registry

import argparse
import json
import math
import os

# the movability contract is ONE contract: whether a field carries a scalar
# sweep is decided in exactly one place, and both the search and this round ask
# the same question of it
from calibrate import sweep_interval as _sweep_interval

BOARDING_BASIS = 'boardings'


def _resolve_run(name_or_path):
    return _results_store.resolve(name_or_path) or name_or_path


def load_fit(run_dir):
    path = os.path.join(run_dir, '_fit.json')
    if not os.path.exists(path):
        raise SystemExit(
            '%s has no _fit.json. Run extract_metrics.py then fit.py on it '
            'first: a step proposed from no fit is a step proposed from '
            'nothing.' % run_dir)
    return json.load(open(path, encoding='utf-8'))


def rows_by_mode(fit):
    g = fit.get('goal_modes') or {}
    if g.get('max_abs_rel_pct') is None:
        raise SystemExit(
            'this run carries no scorable twelve-mode reading (%s). The step is '
            'computed from the board\'s own deviations, so there is nothing to '
            'invert.' % g.get('reason', 'no reason recorded'))
    return {r['mode']: r for r in g.get('modes', [])}, g


def ratio_of(row):
    """modelled / target, from the board's own deviation. None if unscorable."""
    dev = row.get('deviation_pct')
    if dev is None:
        return None
    r = 1.0 + float(dev) / 100.0
    return r if r > 0 else None


def propose(fit, cfg, reference='car'):
    """One damped round. Returns the proposal; moves nothing."""
    rows, g = rows_by_mode(fit)
    mode_to_key = cfg.get('CAL.asc.mode_to_constant')
    damping = float(cfg.get('CAL.asc.damping'))
    max_step = float(cfg.get('CAL.asc.max_step_utils'))

    ref_row = rows.get(reference)
    ref_ratio = ratio_of(ref_row) if ref_row else None
    if not ref_ratio:
        raise SystemExit(
            'the reference mode %r has no scorable deviation on this run, so no '
            'step is identified: an alternative-specific constant is only ever '
            'defined RELATIVE to the reference.' % reference)
    ref_term = math.log(1.0 / ref_ratio)

    proposals, refused = [], []
    for mode, key in sorted(mode_to_key.items()):
        if mode == reference:
            refused.append(dict(mode=mode, key=key, reason=(
                'the reference alternative: its constant is what every other '
                'constant is measured against and it is never moved')))
            continue
        field = cfg.field(key) if hasattr(cfg, 'field') else None
        if field is None:
            refused.append(dict(mode=mode, key=key, reason=(
                'no such registry field: the mode has no declared constant, so '
                'there is nothing to move. Declare one before asking for a '
                'step.')))
            continue
        if 'held_fixed' in field:
            refused.append(dict(
                mode=mode, key=key, held_fixed=True,
                reason=(field['held_fixed'].get('rule') or '')[:400],
                note='REFUSED STRUCTURALLY. Which constants are open is a '
                     'decision recorded in the registry, never one this loop '
                     'makes.'))
            continue
        # No scalar sweep means the registry has declared this constant not
        # movable, and `calibrate.free_parameters` applies the same test. It is
        # not always a freeze: C.asc.motorbike ships `definition` with no sweep
        # because motorbike is a person-level locked carve and is NOT in
        # RUN.mode_choice.modes, so its constant is a level shift that cannot
        # change any choice - a step for it would have a band of exactly zero
        # by construction. Reusing the movability contract rather than
        # re-deciding it here means a constant declared unmovable for ANY
        # reason is refused for that reason, in the registry's own words.
        lo, hi = _sweep_interval(field)
        if lo is None:
            refused.append(dict(
                mode=mode, key=key, no_sweep=True,
                reason=('the registry declares this constant with source %r and '
                        'no scalar sweep, so it is not movable: %s'
                        % (field.get('source'),
                           (field.get('description') or '')[:300]))))
            continue

        row = rows.get(mode)
        ratio = ratio_of(row) if row else None
        if ratio is None:
            refused.append(dict(mode=mode, key=key, reason=(
                'the board scores no deviation for this mode on this run, so '
                'there is no ratio to invert')))
            continue

        raw = math.log(1.0 / ratio) - ref_term
        step = damping * raw
        current = float(field['value'])
        on_boardings = BOARDING_BASIS in (row.get('basis') or '').lower()
        p = dict(mode=mode, key=key, current=current,
                 modelled=row.get('modelled'), target=row.get('target'),
                 deviation_pct=row.get('deviation_pct'),
                 raw_step=round(raw, 6), damping=damping,
                 step=round(step, 6), proposed=round(current + step, 6),
                 abs_step=round(abs(step), 6),
                 sweep=[lo, hi], basis_is_boardings=on_boardings)
        # A proposal outside the field's own declared sweep would be refused by
        # `--config-set` when it was applied, hours later. Say so here instead,
        # and say what it means: the fixed point is asking for a value the
        # project has declared implausible for this constant, which is the same
        # signal as an oversized step arriving by a different route.
        if not (lo <= current + step <= hi):
            p.update(outside_sweep=True, applied=False, reason=(
                'the proposed %.4f falls outside the declared sweep [%.4g, '
                '%.4g]. --config-set would refuse it at apply time; it is '
                'refused here, where the reason is still visible. A fixed point '
                'asking for a value outside the declared range is saying the '
                'residual is not this constant.' % (current + step, lo, hi)))
            refused.append(p)
            continue
        if abs(step) > max_step:
            p.update(refused_step=True, proposed=None, applied=False, reason=(
                'the step is %.3f utils, past CAL.asc.max_step_utils (%.3f). A '
                'constant asked to move this far is not a taste parameter any '
                'more - it is absorbing a mechanism the model does not have. '
                'REFUSED rather than clipped: clipping would hide the one '
                'signal this experiment exists to read.' % (abs(step), max_step)))
            refused.append(p)
            continue
        p['applied'] = True
        proposals.append(p)

    return dict(
        run=fit.get('run'), iteration=g.get('iteration'),
        completion=fit.get('completion'),
        reached_iteration=fit.get('reached_iteration'),
        is_a_result=fit.get('is_a_result'),
        reference_mode=reference, damping=damping,
        max_step_utils=max_step,
        objective_max_abs_rel_pct=g.get('max_abs_rel_pct'),
        worst_mode=g.get('worst_mode'),
        n_inside_pass_band=g.get('n_inside_pass_band'),
        proposals=proposals, refused=refused,
        overrides={p['key']: p['proposed'] for p in proposals},
        note='PROPOSED ONLY. Nothing was run and no registry file was written. '
             'Apply with run_matsim.py --config-set, one per override.')


def contraction(previous, current):
    """Did the step shrink? The whole point of running two rounds."""
    prev = {p['mode']: p for p in previous.get('proposals', [])}
    rows, shrank, grew = [], 0, 0
    for p in current.get('proposals', []):
        q = prev.get(p['mode'])
        if not q:
            continue
        a, b = float(q['abs_step']), float(p['abs_step'])
        row = dict(mode=p['mode'], previous_abs_step=a, this_abs_step=b,
                   ratio=round(b / a, 4) if a else None,
                   shrank=bool(b < a),
                   basis_is_boardings=p.get('basis_is_boardings', False))
        rows.append(row)
        shrank += 1 if b < a else 0
        grew += 1 if b >= a else 0

    share_rows = [r for r in rows if not r['basis_is_boardings']]
    ratios = [r['ratio'] for r in share_rows if r['ratio'] is not None]
    mean_ratio = round(sum(ratios) / len(ratios), 4) if ratios else None
    if mean_ratio is None:
        verdict = ('UNDETERMINED: no mode appears in both rounds with a '
                   'share-basis step, so there is nothing to compare.')
    elif mean_ratio < 1.0:
        verdict = (
            'CONTRACTING (mean step ratio %.3f over %d share-basis modes). The '
            'residual behaves like a taste the constants had not been set to: '
            'further rounds should close it, and the fixed point is the right '
            'instrument.' % (mean_ratio, len(ratios)))
    else:
        verdict = (
            'NOT CONTRACTING (mean step ratio %.3f over %d share-basis modes). '
            'The residual is NOT a constant. No amount of ASC adjustment will '
            'close these modes and the deficit is a mechanism the model does '
            'not contain - which is the answer this experiment was run to get, '
            'and it is worth more than a closed gap.' % (mean_ratio, len(ratios)))
    return dict(modes=rows, n_shrank=shrank, n_grew=grew,
                mean_step_ratio_share_basis=mean_ratio, verdict=verdict,
                note='Computed over SHARE-basis modes only. A boardings-basis '
                     'ratio is a monotone proxy for the logit inversion, not '
                     'the inversion itself, so it is reported per mode and '
                     'excluded from the verdict.')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--out')
    ap.add_argument('--previous',
                    help='a previous round\'s proposal; adds the contraction '
                         'diagnostic, which is what the two-round test reads')
    ap.add_argument('--scenario')
    ap.add_argument('--day')
    a = ap.parse_args()

    desc = _city.descriptor()
    scenario = a.scenario or desc['intervention']['base_scenario']
    run_dir = _resolve_run(a.run) if not os.path.isdir(a.run) else a.run
    fit = load_fit(run_dir)
    day = a.day or fit.get('day')
    cfg = _registry.load(scenario=scenario, day=day)

    out = propose(fit, cfg)
    if a.previous:
        out['round_over_round'] = contraction(
            json.load(open(a.previous, encoding='utf-8')), out)

    print('ASC fixed point, one damped round (damping %.3g, reference %s)'
          % (out['damping'], out['reference_mode']))
    print('read from %s at iteration %s (%s)'
          % (out['run'], out['iteration'], out['completion'] or 'no record'))
    if not out['is_a_result']:
        print('  NOT A RESULT: this run did not run to its last iteration. The '
              'reading is citable at iteration %s and nowhere past it.'
              % out['reached_iteration'])
    print('  objective (max |deviation|) %.4g%% on %s; %s mode(s) inside the band'
          % (out['objective_max_abs_rel_pct'], out['worst_mode'],
             out['n_inside_pass_band']))
    print('\n%-12s %10s %10s %9s %10s %10s' % ('mode', 'dev%', 'current',
                                               'raw', 'step', 'proposed'))
    for p in out['proposals']:
        print('%-12s %10.1f %10.4f %9.4f %10.4f %10.4f%s'
              % (p['mode'], p['deviation_pct'], p['current'], p['raw_step'],
                 p['step'], p['proposed'],
                 '  [boardings proxy]' if p['basis_is_boardings'] else ''))
    if out['refused']:
        print('\nrefused:')
        for r in out['refused']:
            print('  %-12s %s' % (r['mode'], (r.get('reason') or '')[:96]))
    rr = out.get('round_over_round')
    if rr:
        print('\nround over round - THE MEASUREMENT THIS EXPERIMENT EXISTS FOR')
        print('%-12s %14s %12s %8s' % ('mode', 'previous |step|',
                                       'this |step|', 'ratio'))
        for r in rr['modes']:
            print('%-12s %14.4f %12.4f %8s%s'
                  % (r['mode'], r['previous_abs_step'], r['this_abs_step'],
                     '%.3f' % r['ratio'] if r['ratio'] is not None else '-',
                     '  [boardings proxy]' if r['basis_is_boardings'] else ''))
        print('\n%s' % rr['verdict'])

    if a.out:
        json.dump(out, open(a.out, 'w', newline='\n'), indent=2)
        print('\n-> %s' % a.out)
    print('\nPROPOSED ONLY. Apply with:')
    for k, v in sorted(out['overrides'].items()):
        print('   --config-set %s=%g' % (k, v))


if __name__ == '__main__':
    main()
